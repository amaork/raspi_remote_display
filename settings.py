# -*- coding: utf-8 -*-
__all__ = ['RaspiModeManager']


class RaspiModeManager(object):
    DMTModes = {
        '640x480': 4,
        '800x600': 8,
        '1024x768': 16,
        '1280x768': 23,
        '1280x800': 28,
        '1280x960': 32,
        '1280x1024': 35,
        '1366x768': 39,
        '1400x1050': 42,
        '1440x900': 47,
        '1600x1200': 51,
        '1680x1050': 58,
        '1920x1080': 82,
    }

    def __init__(self):
        self.__default_modes = self.DMTModes

    def get_modes(self):
        return self.__default_modes

    def get_index_from_resolution(self, res):
        return self.__default_modes.keys().index(res)


