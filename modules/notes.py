import sqlite3
import logging
import json

logger = logging.getLogger(__name__)

class Notes():
    def __init__(self, config):
        logging.basicConfig(filename=f"{config['log_directory']}/latest.log", level=logging.INFO)
        self.notebook_path = config['notebook_db_path']
        self.interface = config['interface']
        self.functions = config['functions']
        self.max_notes = config['max_notes'] if 'max_notes' in config else 10
        self.__create_metadata()
        self.__create_notebooks()
        self.__create_tags()

    def __create_notebooks(self):
        conn = sqlite3.connect(self.notebook_path)
        cursor = conn.cursor()
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS notebooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notebook TEXT
                )
            ''')
        conn.commit()
        conn.close
    
    def __create_metadata(self):
        conn = sqlite3.connect(self.notebook_path)
        cursor = conn.cursor()
        cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    attr TEXT,
                    value TEXT
                )
            ''')
        conn.commit()
        conn.close

    def __create_tags(self):
        conn = sqlite3.connect(self.notebook_path)
        cursor = conn.cursor()
        cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag TEXT UNIQUE
                )
            ''')
        conn.commit()
        conn.close
    
    def _context(self, config):
        context = "You can also create and manage notebooks. Notebooks are text databases you can use to jot down lists. If the user wants to save text, try to fit the request to the notebook functions. Below is a list of notebook names to use with the notebook functions:"
        try:
            # GET TABLES

            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            cursor.execute("SELECT notebook FROM notebooks")
            notebooks = cursor.fetchall()
            conn.close()
            
            notebook_list = [notebook[0] for notebook in notebooks] # maybe append this as a json
            context += "\n" + ", ".join(notebook_list)

            # GET TAGS

            context += "\nBelow is a list of tags to use with the notebook functions:"
            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            cursor.execute("SELECT tag FROM tags")
            tags = cursor.fetchall()
            conn.close()
            
            tag_list = [tag[0] for tag in tags] # mabye append this as a json
            context += "\n" + "\n".join(tag_list)
            context += "\n"

            return context
        except Exception as e:
            logging.error(e)
            return context

    def create_notebook(self, notebook: str, description: str, tags: list):
        """Creates a notebook with the specified name."""
        try:
            # clean inputs
            notebook = notebook.replace(" ", "_")
            notebook = notebook.lower()
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]

            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()

            cursor.execute("SELECT notebook FROM notebooks WHERE notebook = ?", (notebook,))
            if cursor.fetchone():
                return

            print("Creating notebook")
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {notebook} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    note TEXT
                )
            ''')

            print("Inserting notebook into notebooks table")
            cursor.execute(f"INSERT INTO notebooks (notebook) VALUES ('{notebook}')")
            
            print("Inserting attributes into metadata table")
            for tag in tags:
                cursor.execute(f"INSERT INTO metadata (table_name, attr, value) VALUES (?, 'tag', ?)", (notebook, tag,))
                cursor.execute("INSERT OR IGNORE INTO tags (tag) VALUES (?)", (tag,))
            cursor.execute(f"INSERT INTO metadata (table_name, attr, value) VALUES (?, 'desc', ?)", (notebook, description,))

            conn.commit()
            conn.close()
            self.interface.say_canned("notebook_created")
        except Exception as e:
            logging.error(e)
    create_notebook.variables={"notebook": "The name of the new notebook.", "description": "A string describing what the table is for", "tags": "A list of single-words that are relevant to the table."}

    def add_notes(self, notes: list, notebook: str):
        """Inserts new notes to a specified notebook."""
        try:
            # Clean inputs
            notebook = notebook.replace(" ", "_")
            notebook = notebook.lower()
            if isinstance(notes, str):
                notes = [note.strip() for note in notes.split(',')]

            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            cursor.execute("SELECT notebook FROM notebooks WHERE notebook = ?", (notebook,))
            if not cursor.fetchone():
                raise Exception("notebook_not_exist")
            for note in notes:
                cursor.execute(f"INSERT INTO {notebook} (note) VALUES (?)", (note,))
            
            conn.commit()
            conn.close()
            self.interface.say_canned("note_inserted")
        except Exception as e:
            logging.error(e)
    add_notes.variables={"notes": "A list of notes to insert.", "notebook": "The table/notebook to insert the notes into."}

    def delete_note(self, note_desc: list[str], notebook: str):
        try:
            notebook = notebook.replace(" ", "_")
            notebook = notebook.lower()
            if isinstance(note_desc, str):
                note_desc = [desc.strip() for desc in note_desc.split(',')]

            # Give ai all notes from table with ids and tell it to return the id most similar to description
            all_notes = self.__get_all_notes(notebook)
            next_context = f"Below is a list of notes with their corresponding id. Respond with a json list of ids that most fits the description of \"{note_desc}\". Only respond with the raw json list, no words or formatting.\n"
            note_descs = {}
            for note in all_notes:
                next_context+=f"{note[0]}: {note[1]}\n"                
                note_descs[note[0]] = note[1]
            self.interface.clear_last_prompt()
            
            ids = json.loads(self.functions['prompt'](next_context))
            
            # ask the user if they want to delete note {note_text}
            if len(ids) > 1:
                self.interface.say_canned("multiple_notes_delete")
            else:
                self.interface.say(f"Delete '{note_descs[ids[0]]}'?")

            # get response
            confirmation = self.interface.get_input().split(" ")

            # delete note if yes
            confirmation = confirmation[::-1] # reverse confirmations for cases like 'yeah, no' and 'no... yeah'
            for word in confirmation:
                if word in self.interface.affirmations:
                    for id in ids:
                        self.__delete_note(note_id=id, notebook=notebook)
                    self.interface.say_canned("note_deleted")
                    break
                elif word in self.interface.quit_terms:
                    self.interface.say_canned("note_delete_cancel")
                    break
        except Exception as e:
            self.interface.say_canned(e)
    delete_note.variables={"note_desc": "The list of descriptions describing each note to delete.", "notebook": "The notebook to delete a note from."}

    def __delete_note(self, note_id: int, notebook: str):
        try:
            # Clean inputs
            notebook = notebook.replace(" ", "_")
            notebook = notebook.lower()

            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            cursor.execute("SELECT notebook FROM notebooks WHERE notebook = ?", (notebook,))
            if not cursor.fetchone():
                raise Exception("notebook_not_exist")
            cursor.execute(f"DELETE FROM {notebook} WHERE id = ?", (note_id,))
            
            conn.commit()
            conn.close()
            self.interface.say_canned("note_deleted")
        except Exception as e:
            logging.error(e)

    def __get_all_notes(self, notebook: str):
        try:
            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, note FROM {notebook}".format(notebook=notebook))
            notes = cursor.fetchall()
            conn.close()
            return [(note[0], note[1]) for note in notes]
        except Exception as e:
            logging.error(e)
            return []

    def find_note_from_tags(self, tags: list):
        """Searches for a note using the given tags. Only call this if it is ambiguous what table the note may be from. Otherwise use find_note_from_table."""
        # Add list of tables that match that tag to previous prompt and tell to call
        try:
            conn = sqlite3.connect(self.notebook_path)
            cursor = conn.cursor()
            # Find tables that contain any of the tags in the metadata table

            # Get tables that match tag
            query = "SELECT table_name FROM metadata WHERE value IN ({}) AND attr='tag'".format(','.join('?' for _ in tags))
            cursor.execute(query, tags)
            tables = cursor.fetchall()
            tables = [table[0] for table in tables]
            tables = list(set(tables))

            # Get description to pair with table
            query = f"SELECT table_name, value FROM metadata WHERE table_name IN ({','.join('?' for _ in tables)}) AND attr='desc'"
            cursor.execute(query, tables)
            tables = cursor.fetchall()
            tables = [(table[0], table[1]) for table in tables]
            conn.close()
            next_prompt="Below is a list of tables and descriptions that match a relevant tag to the previous prompt. Call find_notes_in_notebook with the table that most closely matches to what the user wants:"
            for table in tables:
                next_prompt += f"{table[0]} - {table[1]}"
            
            self.functions['prompt'](next_prompt)
        except Exception as e:
            logging.error(e)
            return None
    find_note_from_tags.variables={"tags": "The list of single-word, relevant tags to search for."}

    def get_notes_in_notebook(self, notebook: str):
        """Searches and displays notes to a used based on previous context."""
        notebook = notebook.replace(" ", "_")
        notebook = notebook.lower()
        all_notes = [note[1] for note in self.__get_all_notes(notebook)]
        next_prompt = ""
        for entry in reversed(self.interface.context):
            if entry['content'][0]['type'] == 'text':
                next_prompt += entry['content'][0]['text']
                break
        next_prompt += "\nYou have previously called get_notes_in_notebook, below is the list of information in the relevant requested table:\n"
        if len(all_notes) == 0:
            next_prompt += "There are no notes in this notebook."
        else:
            for i in range(0, len(all_notes)):
                next_prompt += f"{i+1}. {all_notes[i]}\n"
        
        message = self.functions['prompt'](next_prompt)
        if message:
            self.functions['say'](message)
        self.interface.clear_last_prompt()
    get_notes_in_notebook.variables={"notebook": "The notebook to search in."}

