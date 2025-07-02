# Class managing json file input/output
# Read/Write json file : self.path_json
# Read/Write json content : self.content_json
import codecs
import json
import os
from json import JSONDecodeError
import jsonpickle


class FileJson:

    def __init__(self, path_json, default_content_json):
        # Init json file path
        self.default_content_json = default_content_json
        self.content_json = self.default_content_json
        self.path_json = path_json

        # If file does not exist
        if not self.is_exists():
            # Create default element
            print("Create " + path_json)
            self.write_content()
        else:
            # Load content json
            self.read_content()

    def get_content(self):
        try:
            # Get content from json file
            serialized = ""
            json_object_data = open(self.path_json, "rb").readlines()
            for d in json_object_data:
                serialized = serialized + d.decode()
            data = jsonpickle.decode(serialized)

            if type(self.default_content_json) != type(data):
                print("TypeError : " + str(type(self.default_content_json)))
                print("TypeError : " + str(type(data)))
                print("Bad format")
                return self.default_content_json
            else:
                return data

        except TypeError as MyError:
            print("TypeError : return self.default_content_json")
            print("TypeError : " + str(MyError))
            return self.default_content_json
        except JSONDecodeError:
            print("JSONDecodeError : return self.default_content_json")
            return self.default_content_json

    def read_content(self):
        try:
            self.content_json = self.get_content()
        except TypeError:
            pass

    def set_content(self, content_json):
        try:
            # Set content to json file
            file = codecs.open(self.path_json, 'w', "utf-8")
            serialized = jsonpickle.encode(content_json)
            json_object = json.loads(serialized)
            file.write(json.dumps(json_object, indent=2, ensure_ascii=False))
        except TypeError:
            pass

    def write_content(self):
        self.set_content(self.content_json)

    def is_exists(self):
        return os.path.exists(self.path_json)