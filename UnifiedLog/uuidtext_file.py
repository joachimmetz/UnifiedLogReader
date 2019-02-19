# -*- coding: utf-8 -*-
'''The uuidtext file parser.'''

from __future__ import unicode_literals

import struct
import os
import posixpath

from UnifiedLog import dtfabric_parser
from UnifiedLog import errors
from UnifiedLog import logger


class Uuidtext(dtfabric_parser.DtFabricBaseParser):
    '''Uuidtext file parser.'''

    _DEFINITION_FILE = 'dtfabric.yaml'

    _FILE_SIGNATURE = 0x66778899

    def __init__(self, v_file, uuid):
        '''Initializes an uuidtext file parser.

        Args:
          v_file (VirtualFile): a virtual file.
          uuid (uuid.UUID): an UUID.
        '''
        super(Uuidtext, self).__init__()
        self._file = v_file
        self.entries = []   # [ [range_start_offset, data_offset, data_len], [..] , ..]
        self.library_path = ''
        self.library_name = ''
        self.Uuid = uuid

    def _ParseFileObject(self, file_object):
        '''Parses an uuidtext file-like object.

        Args:
          file_object (file): file-like object.

        Raises:
          ParseError: if the uuidtext file cannot be parsed.
        '''
        file_header_map = self._GetDataTypeMap('uuidtext_file_header')

        file_header, data_offset = self._ReadStructureFromFileObject(
            file_object, 0, file_header_map)

        if file_header.signature != self._FILE_SIGNATURE:
            raise errors.ParseError(
                'Unsupported signature: 0x{0:04x}.'.format(file_header.signature))

        format_version = (
            file_header.major_format_version, file_header.minor_format_version)
        if format_version != (2, 1):
            raise errors.ParseError(
                'Unsupported format version: {0:d}.{1:d}.'.format(
                    file_header.major_format_version,
                    file_header.minor_format_version))

        for entry_descriptor in file_header.entry_descriptors:
            entry_tuple = (
                entry_descriptor.offset, data_offset, entry_descriptor.size)
            self.entries.append(entry_tuple)
            data_offset += entry_descriptor.size

        file_footer_map = self._GetDataTypeMap('uuidtext_file_footer')

        file_footer, _ = self._ReadStructureFromFileObject(
            file_object, data_offset, file_footer_map)

        self.library_path = file_footer.library_path
        self.library_name = posixpath.basename(self.library_path)

    def ReadFmtStringFromVirtualOffset(self, v_offset):
        if not self._file.is_valid:
            return '<compose failure [UUID]>' # value returned by 'log' program if uuidtext is not found

        if v_offset & 0x80000000:
            return '%s' # if highest bit is set

        for entry in self.entries:
            if (entry[0] <= v_offset) and ((entry[0] + entry[2]) > v_offset):
                rel_offset = v_offset - entry[0]
                f = self._file.file_pointer
                f.seek(entry[1] + rel_offset)
                buffer = f.read(entry[2] - rel_offset)
                return self._ReadCString(buffer)

        #Not found
        logger.error('Invalid bounds 0x{:X} for {}'.format(v_offset, str(self.Uuid))) # This is error msg from 'log'
        return '<compose failure [UUID]>'

    def Parse(self):
        '''Parses a uuidtext file.

        self._file.is_valid is set to False if this method encounters issues
        parsing the file.

        Returns:
          bool: True if the dsc file-like object was successfully parsed,
              False otherwise.
        '''
        file_object = self._file.open()
        if not file_object:
          return False

        result = True
        try:
            self._ParseFileObject(file_object)
        except errors.ParseError:
            logger.exception('Uuidtext Parser error')
            result = False

        if not result:
            self._file.is_valid = False

        return result
