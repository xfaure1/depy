from tools.data_cfg import DataCfg
from tools.file_json import FileJson


class Cfg(FileJson):

    def __init__(self):
        super(Cfg, self).__init__("config.json", DataCfg())

    def get_mode_generate(self):
        return self.get_content().mode_generate

    def get_height_rectangle(self, split_height, full_height):
        if self.get_content().is_center_state_text:
            return full_height

        return split_height

    def is_reset_color_search(self):
        return self.get_content().is_reset_color_search

    def is_reset_representation_circle(self):
        return self.get_content().is_reset_representation_circle

    def is_diagonal_visible(self):
        return self.get_content().is_diagonal_visible

    def is_used_diagonal(self):
        return self.get_content().is_used_diagonal


CFG = Cfg()



