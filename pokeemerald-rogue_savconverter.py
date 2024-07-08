#!/usr/bin/python

import struct
import shutil
import argparse
import os
from operator import xor

###################################################
# Define the constants for the different versions #
###################################################
##
# Globals for the 2.0 version
SECTOR_DATA_SIZE_V2   = 4084
SECTOR_FOOTER_SIZE_V2 = 12
NPOKEMON_V2 = 905
##
# Globals for the 1.3.2 version
SECTOR_DATA_SIZE_V1 = 3968
SECTOR_FOOTER_SIZE_V1 = 128
NPOKEMON_V1 = 898

##
# Common globals
NSECTORS = 32
ROGUESAVEVERSION_OFFSET = 2498

PC_ITEMS_COUNT = 50
PLAYERPARTY_COUNTOFFSET = 0x234
FIRSTPKMN_OFFSET = 0x238
FIRSTPKMN_IN_BOX_OFFSET = 4
PKMNBOX_STRUCT_SIZE = 80

SECTOR_DATA_SIZE = SECTOR_DATA_SIZE_V1 # The initial value will be altered whithin the function "prepareGlobalsForVersion"
SECTOR_FOOTER_SIZE = SECTOR_FOOTER_SIZE_V1
SECTOR_SIZE = SECTOR_DATA_SIZE + SECTOR_FOOTER_SIZE

PLAYER_NAME_LENGTH = 7
TRAINER_ID_LENGTH = 4
PARTY_SIZE = 6
TOTAL_BOXES = 10
PKMN_PER_BOX = 30

SHINY_ODDS = 655

SAVE_SECTOR_STRUCT = None


def prepareGlobalsForVersion(ver):
    """
        Configure appropiately several globals that depends on the version of the .sav file.
        
        :param ver: Two possible values. 1 for 1.3.2 .sav style; 2 for the newest format.
    """
    global SECTOR_DATA_SIZE, SECTOR_FOOTER_SIZE, sector_format_string, SAVE_SECTOR_STRUCT
    global PKMN_STRUCT_SIZE, ENCRIPTIONKEY_OFFSET,MONEY_OFFSET,PCITEMS_OFFSET,ITEMS_OFFSET
    global BAG_ITEM_CAPACITY,DEXSEEN_OFFSET,DEXSIZE,DEXCAUGHT_OFFSET

    if ver == 1: # v1.3.2
        PKMN_STRUCT_SIZE  = 100
        ENCRIPTIONKEY_OFFSET = 0xac
        MONEY_OFFSET = FIRSTPKMN_OFFSET + PARTY_SIZE*PKMN_STRUCT_SIZE
        PCITEMS_OFFSET = MONEY_OFFSET + 4 + 4
        ITEMS_OFFSET = PCITEMS_OFFSET + PC_ITEMS_COUNT*4 # PC_ITEMS_COUNT items max at the PC
        BAG_ITEM_CAPACITY = 30 + 30 + 16 + 64 + 46
        DEXSEEN_OFFSET = 0x3598
        DEXSIZE = 113     # Bytes
        DEXCAUGHT_OFFSET = DEXSEEN_OFFSET+DEXSIZE
        SECTOR_DATA_SIZE = SECTOR_DATA_SIZE_V1
        SECTOR_FOOTER_SIZE = SECTOR_FOOTER_SIZE_V1
        # Define the structure format
        # 'SECTOR_DATA_SIZE' bytes for data
        # 'SECTOR_FOOTER_SIZE - 12' bytes for unused portion
        # 'H' for id (u16)
        # 'H' for checksum (u16)
        # 'I' for security (u32)
        # 'I' for counter (u32)
        sector_format_string = f'{SECTOR_DATA_SIZE}s{SECTOR_FOOTER_SIZE - 12}xHHII'
    else:
        SECTOR_DATA_SIZE = SECTOR_DATA_SIZE_V2
        SECTOR_FOOTER_SIZE = SECTOR_FOOTER_SIZE_V2
        sector_format_string = f'{SECTOR_DATA_SIZE}sHHII'
        PKMN_STRUCT_SIZE  = 104 # In bytes
        ENCRIPTIONKEY_OFFSET = 0x4c
        MONEY_OFFSET = FIRSTPKMN_OFFSET + PARTY_SIZE*PKMN_STRUCT_SIZE
        PCITEMS_OFFSET = MONEY_OFFSET + 4 + 4
        ITEMS_OFFSET = PCITEMS_OFFSET + PC_ITEMS_COUNT*4 # PC_ITEMS_COUNT items max at the PC
        BAG_ITEM_CAPACITY = 450
        DEXSEEN_OFFSET = 0x30b4
        DEXSIZE = 191     # Bytes
        DEXCAUGHT_OFFSET = DEXSEEN_OFFSET+DEXSIZE
    SAVE_SECTOR_STRUCT = struct.Struct(sector_format_string)



##################
# Misc functions #
##################
def backupFileIfNeeded(ifile, ofile):
    """
    Check if the output file exists. If it does, do nothing.
    Otherwise, create a backup of the input file with the name of the output file.
    
    :param ifile: Path to the input file to be backed up.
    :param ofile: Path to the output file (backup file).
    """
    # Check if the output file exists
    if os.path.exists(ofile):
        print(f"Output file '{ofile}' already exists. No action taken.")
    else:
        try:
            # Copy the input file to the output file location
            shutil.copy2(ifile, ofile)
            print(f"Backup created: '{ofile}'")
        except Exception as e:
            print(f"Error while creating backup: {e}")


def decodeString(text):
    """
    Pokemon strings are not coded in ASCII/UTF-8. They use their own encoding. 
    I found a previous project in Github (https://github.com/ads04r/Gen3Save.git).
    It does not always work properly, it should be reviewed, but no modification is being
    applied over the strings, so it was only used for debugging purposes

    :param text: Pokemon-style encoded string
    :return: An ASCII text representation
    """
    chars = "0123456789!?.-         ,  ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    ret = ""
    for i in text:
        c = int(i) - 161
        if c<0 or c>len(chars):
            ret = ret + " "
        else:
            ret = ret + chars[c]
    return ret.strip()

def calculateChecksum(data, size):
    """
    Calculate a checksum for a saved slot.

    :param data: A bytes object containing the data.
    :param size: The size of the data.
    :return: The calculated checksum as an integer.
    """
    checksum = 0

    for i in range(size // 4):
        # Extract a 4-byte (32-bit) chunk from the data
        chunk = int.from_bytes(data[i*4:(i+1)*4], byteorder='little')
        checksum += chunk

    return ((checksum >> 16) + checksum) & 0xFFFF

def calculateChecksumBox(data, size):
    """
    Calculate a checksum for the given data of a Pokemon (struct PokemonBox).

    :param data: A bytes object containing the data.
    :param size: The size of the data.
    :return: The calculated checksum as an integer.
    """
    checksum = 0

    for i in range(size // 2):
        # Extract a 2-byte (16-bit) chunk from the data
        chunk = int.from_bytes(data[i*2:(i+1)*2], byteorder='little')
        checksum += chunk

    # return ((checksum >> 16) + checksum) & 0xFFFF
    # Note that the checksum is not the same that the one computed for the saved slots
    return checksum & 0xFFFF


############################################################################
# Functions in charge of manipulating the blocks that were saved in memory #
############################################################################
def getSectorDesc(id):
    """
        Given an id of a saved sector, return a description for such ID.
        
        :param id: Identifier of the slot according to the source code of game.
        :return: Human readable description of the block.
    """
    if id == 0:       return "SLOT1_SAVEBLOCK2"
    elif id == 1:     return "SLOT1_SAVEBLOCK1[0]"
    elif id == 2:     return "SLOT1_SAVEBLOCK1[1]"
    elif id == 3:     return "SLOT1_SAVEBLOCK1[2]"
    elif id == 4:     return "SLOT1_SAVEBLOCK1[3]"
    elif id == 5:     return "SLOT1_PKMNSTORAGE[0]"
    elif id == 6:     return "SLOT1_PKMNSTORAGE[1]"
    elif id == 7:     return "SLOT1_PKMNSTORAGE[2]"
    elif id == 8:     return "SLOT1_PKMNSTORAGE[3]"
    elif id == 9:     return "SLOT1_PKMNSTORAGE[4]"
    elif id == 10:    return "SLOT1_PKMNSTORAGE[5]"
    elif id == 11:    return "SLOT1_PKMNSTORAGE[6]"
    elif id == 12:    return "SLOT1_PKMNSTORAGE[7]"
    elif id == 13:    return "SLOT1_PKMNSTORAGE[8]"
    elif id == 14+0:  return "SLOT2_SAVEBLOCK2"
    elif id == 14+1:  return "SLOT2_SAVEBLOCK1[0]"
    elif id == 14+2:  return "SLOT2_SAVEBLOCK1[1]"
    elif id == 14+3:  return "SLOT2_SAVEBLOCK1[2]"
    elif id == 14+4:  return "SLOT2_SAVEBLOCK1[3]"
    elif id == 14+5:  return "SLOT2_PKMNSTORAGE[0]"
    elif id == 14+6:  return "SLOT2_PKMNSTORAGE[1]"
    elif id == 14+7:  return "SLOT2_PKMNSTORAGE[2]"
    elif id == 14+8:  return "SLOT2_PKMNSTORAGE[3]"
    elif id == 14+9:  return "SLOT2_PKMNSTORAGE[4]"
    elif id == 14+10: return "SLOT2_PKMNSTORAGE[5]"
    elif id == 14+11: return "SLOT2_PKMNSTORAGE[6]"
    elif id == 14+12: return "SLOT2_PKMNSTORAGE[7]"
    elif id == 14+13: return "SLOT2_PKMNSTORAGE[8]"
    elif id == 28:    return "HOF[0]"
    elif id == 29:    return "HOF[1]"
    elif id == 30:    return "TRAINERHILL"
    elif id == 31:    return "RECORDEDBATTLE"
    elif id == 65535: return "EMPTY"
    else: return "UNKNOWN"



def processSavedSector(inputPath):
    """
    The information in the main memory of the device is stored in the following way:

        Block 0 of 4096B
        Block 1 of 4096B
        Block 2 of 4096B
        Block 3 of 4096B
        Block ...
        Block 31 of 4096B
    The internal logic of the program will split the different structures in blocks of 4096B.
    Some bytes at the end of the block are reserved (checksum, security bytes), so the total amount
    of useful information is limited.

    This routine will iterate over the file, rebuilding the original structured.

    Example: Let's say that the structure PKMNSTORAGE was splitted among 9 blocks. This routine will
    recover the information in a big merged chunk.


        
        
    :param inputPath: input .sav file
    :return: A dict structure containing the contiguous data of the different structures (SaveBlock{1,2}, PKMNSTORAGE, etc.).
    """
    fOffset = 0
    parsedSectors = {
        'SLOT1_SAVEBLOCK1':   {'data': bytearray(4*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'SLOT1_SAVEBLOCK2':   {'data': bytearray(4*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'SLOT1_PKMNSTORAGE':  {'data': bytearray(9*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'SLOT2_SAVEBLOCK1':   {'data': bytearray(4*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'SLOT2_SAVEBLOCK2':   {'data': bytearray(4*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'SLOT2_PKMNSTORAGE':  {'data': bytearray(9*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'HOF':                {'data': bytearray(2*SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'TRAINERHILL':        {'data': bytearray(SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF},
        'RECORDEDBATTLE':     {'data': bytearray(SECTOR_DATA_SIZE), 'counter':0, 'security':0xFFFFFFFF}
    }
    with open(inputPath, 'rb') as file:
        while True:
            if fOffset>=NSECTORS*SECTOR_SIZE:
                break
            # Read a chunk of SECTOR_SIZE bytes
            sector_data = file.read(SECTOR_SIZE)
            if not sector_data:
                break
            
            # Unpack the data using the struct
            sector_data = SAVE_SECTOR_STRUCT.unpack(sector_data)
            # Extract the fields
            _, id_, checksum, security, counter = sector_data
            data = bytearray(sector_data[0])
            descr = getSectorDesc(id_)
            print(f"=== {descr} (Offset: 0x{fOffset:04X}, Id: {id_}, Checksum: 0x{checksum:04X}, Counter: {counter}, Security: 0x{security:08X})")
            
            if   descr == "SLOT1_SAVEBLOCK1[0]":  block = 'SLOT1_SAVEBLOCK1'; pos = 0
            elif descr == "SLOT1_SAVEBLOCK1[1]":  block = 'SLOT1_SAVEBLOCK1'; pos = 1
            elif descr == "SLOT1_SAVEBLOCK1[2]":  block = 'SLOT1_SAVEBLOCK1'; pos = 2
            elif descr == "SLOT1_SAVEBLOCK1[3]":  block = 'SLOT1_SAVEBLOCK1'; pos = 3
            elif descr == "SLOT1_SAVEBLOCK2":     block = 'SLOT1_SAVEBLOCK2'; pos = 0
            elif descr == "SLOT1_PKMNSTORAGE[0]": block = 'SLOT1_PKMNSTORAGE'; pos = 0
            elif descr == "SLOT1_PKMNSTORAGE[1]": block = 'SLOT1_PKMNSTORAGE'; pos = 1
            elif descr == "SLOT1_PKMNSTORAGE[2]": block = 'SLOT1_PKMNSTORAGE'; pos = 2
            elif descr == "SLOT1_PKMNSTORAGE[3]": block = 'SLOT1_PKMNSTORAGE'; pos = 3
            elif descr == "SLOT1_PKMNSTORAGE[4]": block = 'SLOT1_PKMNSTORAGE'; pos = 4
            elif descr == "SLOT1_PKMNSTORAGE[5]": block = 'SLOT1_PKMNSTORAGE'; pos = 5
            elif descr == "SLOT1_PKMNSTORAGE[6]": block = 'SLOT1_PKMNSTORAGE'; pos = 6
            elif descr == "SLOT1_PKMNSTORAGE[7]": block = 'SLOT1_PKMNSTORAGE'; pos = 7
            elif descr == "SLOT1_PKMNSTORAGE[8]": block = 'SLOT1_PKMNSTORAGE'; pos = 8
            elif descr == "HOF[0]":               block = 'HOF'; pos = 0
            elif descr == "HOF[1]":               block = 'HOF'; pos = 1
            elif descr == "TRAINERHILL":          block = 'TRAINERHILL'; pos = 0
            elif descr == "RECORDEDBATTLE":       block = 'RECORDEDBATTLE'; pos = 0
            else: block = None


            if block and counter >= parsedSectors[block]['counter']:
                parsedSectors[block]['data'][SECTOR_DATA_SIZE*pos:SECTOR_DATA_SIZE*(pos+1)] = data
                parsedSectors[block]['counter']  = counter
                parsedSectors[block]['security'] = security
            fOffset += SECTOR_SIZE
    return parsedSectors



def __writeSector(data, iden, security, counter, ofile):
    checksum = calculateChecksum(data, SECTOR_DATA_SIZE)
    new_sector_data = SAVE_SECTOR_STRUCT.pack(data,iden,checksum,security,counter)
    ofile.write(new_sector_data)


def saveSectors(sectors, outputPath):
    """
    Write the dictionary containing the different information from the sectors to a .sav file
    """
    security = sectors['SLOT1_SAVEBLOCK2']['security']
    counter = sectors['SLOT1_SAVEBLOCK2']['counter'] + 1
    if counter & 0x1: # The slot 1 is only used for even counters
        counter += 1
    emptyId = 0xFFFF
    invalidSecurity = 0xFFFFFFFF
    with open(outputPath, 'wb') as ofile:
        id_ = 0
        __writeSector(sectors['SLOT1_SAVEBLOCK2']['data'][:SECTOR_DATA_SIZE], id_, security, counter, ofile); id_+=1
        for i in range(4):
            __writeSector(sectors['SLOT1_SAVEBLOCK1']['data'][i*SECTOR_DATA_SIZE:(i+1)*SECTOR_DATA_SIZE], id_, security, counter, ofile); id_+=1
        for i in range(9):
            __writeSector(sectors['SLOT1_PKMNSTORAGE']['data'][i*SECTOR_DATA_SIZE:(i+1)*SECTOR_DATA_SIZE], id_, security, counter, ofile); id_+=1
        __writeSector(sectors['SLOT2_SAVEBLOCK2']['data'][:SECTOR_DATA_SIZE], emptyId, invalidSecurity, 0, ofile); id_+=1
        for i in range(4):
            __writeSector(sectors['SLOT2_SAVEBLOCK1']['data'][i*SECTOR_DATA_SIZE:(i+1)*SECTOR_DATA_SIZE], emptyId, invalidSecurity, 0, ofile); id_+=1
        for i in range(9):
            __writeSector(sectors['SLOT2_PKMNSTORAGE']['data'][i*SECTOR_DATA_SIZE:(i+1)*SECTOR_DATA_SIZE], emptyId, invalidSecurity, 0, ofile); id_+=1
        if sectors['HOF']['security']==invalidSecurity:
            hofId = emptyId
        else:
            hofId = id_
        for i in range(2):
            __writeSector(sectors['HOF']['data'][i*SECTOR_DATA_SIZE:(i+1)*SECTOR_DATA_SIZE], hofId, sectors['HOF']['security'], counter, ofile); id_+=1;
            if hofId!=emptyId: hofId+=1
        if sectors['TRAINERHILL']['security']==invalidSecurity:
            trainId = emptyId
        else:
            trainId = id_
        __writeSector(sectors['TRAINERHILL']['data'][:SECTOR_DATA_SIZE], trainId, sectors['TRAINERHILL']['security'], counter, ofile); id_+=1
        if sectors['TRAINERHILL']['security']==invalidSecurity:
            batId = emptyId
        else:
            batId = id_
        __writeSector(sectors['RECORDEDBATTLE']['data'][:SECTOR_DATA_SIZE], batId, sectors['RECORDEDBATTLE']['security'], counter, ofile); id_+=1
    return



###########################################################################
# Routines that interact with the PokemonStructures (!= Blocks in memory) #
###########################################################################

###
# 1. Mon routines
def printMon(pkmDict):
    """
    Print a mon to the standard output
    """
    if pkmDict['box'] == 0:
        print(f"     < PARTY  N{pkmDict['pos']:02} > Pokemon #{pkmDict['data']['nPkmn']} named '{pkmDict['data']['pkmnName']}'  (Shiny: {pkmDict['data']['shiny']})")
    else:
        print(f"     < BOX {pkmDict['box']:02} N{pkmDict['pos']:02} > Pokemon #{pkmDict['data']['nPkmn']} named '{pkmDict['data']['pkmnName']}'  (Shiny: {pkmDict['data']['shiny']})")


def getTypes(rawData, personality):
    """
    The structure of a mon is complicated, because the data is not always stored in the same way.
    It depends of the personality of the mon. This routine will return the type{0,1,2,3} structures
    in the natural order 
    """
    ret = bytearray(48)
    mod = personality % 24
    if mod ==  0: pos=[0,1,2,3]
    elif mod ==  1: pos=[0,1,3,2]
    elif mod ==  2: pos=[0,2,1,3]
    elif mod ==  3: pos=[0,3,1,2]
    elif mod ==  4: pos=[0,2,3,1]
    elif mod ==  5: pos=[0,3,2,1]
    elif mod ==  6: pos=[1,0,2,3]
    elif mod ==  7: pos=[1,0,3,2]
    elif mod ==  8: pos=[2,0,1,3]
    elif mod ==  9: pos=[3,0,1,2]
    elif mod == 10: pos=[2,0,3,1]
    elif mod == 11: pos=[3,0,2,1]
    elif mod == 12: pos=[1,2,0,3]
    elif mod == 13: pos=[1,3,0,2]
    elif mod == 14: pos=[2,1,0,3]
    elif mod == 15: pos=[3,1,0,2]
    elif mod == 16: pos=[2,3,0,1]
    elif mod == 17: pos=[3,2,0,1]
    elif mod == 18: pos=[1,2,3,0]
    elif mod == 19: pos=[1,3,2,0]
    elif mod == 20: pos=[2,1,3,0]
    elif mod == 21: pos=[3,1,2,0]
    elif mod == 22: pos=[2,3,1,0]
    elif mod == 23: pos=[3,2,1,0]
    for i in range(len(pos)):
        if   i==0: ret[:12]   = rawData[32+(pos[i]*12):32+((pos[i]+1)*12)]
        elif i==1: ret[12:24] = rawData[32+(pos[i]*12):32+((pos[i]+1)*12)]
        elif i==2: ret[24:36] = rawData[32+(pos[i]*12):32+((pos[i]+1)*12)]
        elif i==3: ret[36:48] = rawData[32+(pos[i]*12):32+((pos[i]+1)*12)]
    return ret[:12],ret[12:24],ret[24:36],ret[36:48]


def setTypes(rawData, types, personality):
    """
    If the structure of a mon has been reordered for its use, when writing again it must be returned
    to the original format. This function is related to "getTypes"
    """
    mod = personality % 24
    if mod ==  0: pos=[0,1,2,3]
    elif mod ==  1: pos=[0,1,3,2]
    elif mod ==  2: pos=[0,2,1,3]
    elif mod ==  3: pos=[0,3,1,2]
    elif mod ==  4: pos=[0,2,3,1]
    elif mod ==  5: pos=[0,3,2,1]
    elif mod ==  6: pos=[1,0,2,3]
    elif mod ==  7: pos=[1,0,3,2]
    elif mod ==  8: pos=[2,0,1,3]
    elif mod ==  9: pos=[3,0,1,2]
    elif mod == 10: pos=[2,0,3,1]
    elif mod == 11: pos=[3,0,2,1]
    elif mod == 12: pos=[1,2,0,3]
    elif mod == 13: pos=[1,3,0,2]
    elif mod == 14: pos=[2,1,0,3]
    elif mod == 15: pos=[3,1,0,2]
    elif mod == 16: pos=[2,3,0,1]
    elif mod == 17: pos=[3,2,0,1]
    elif mod == 18: pos=[1,2,3,0]
    elif mod == 19: pos=[1,3,2,0]
    elif mod == 20: pos=[2,1,3,0]
    elif mod == 21: pos=[3,1,2,0]
    elif mod == 22: pos=[2,3,1,0]
    elif mod == 23: pos=[3,2,1,0]
    for i in range(len(pos)):
        rawData[32+(pos[i]*12):32+((pos[i]+1)*12)]=types[i]
    return rawData

def decryptTypes(rawType, key):
    """
        The data of the struct PokemonBox (bytes 32 to 80) is encrypted with an XOR key.
        This routine basically overwrite the ciphered content with the clear one.

        As it is a XOR Key, the same routine can encrypt/decrypt the content (symmetrical algorithm)

    """
    for i in range(3):
        w = struct.unpack('<I', rawType[i*4:(i+1)*4])[0]
        rawType[i*4:(i+1)*4] = struct.pack('<I', xor(key, w))
    return rawType

def createMon(ba, version):
    """
    From a byte array representing a mon, and the version of such bytearray (1 for 1.3.2; 2 for 2.0 .sav file)
    return a dictionary with the different characteristics. 
    """
    pkm = ba
    personality = struct.unpack('<I', pkm[0:4])[0]
    trainerId   = struct.unpack('<I', pkm[4:8])[0]
    cPkmnName   = pkm[8:18]
    pkmnName    = decodeString(cPkmnName)
    lang        = pkm[18]
    if version == 2:
        hiddenNatureModifier = lang>>3
        lang &= 0x7
    else:
        hiddenNatureModifier = 0
    EggSpecies  = pkm[19]
    cTrainerName = pkm[20:27]
    trainerName = decodeString(cTrainerName)
    markings    = pkm[27]
    checksum    = struct.unpack('<H', pkm[28:30])[0]
    unknown    = struct.unpack('<H', pkm[30:32])[0]
    # 30-31 -> unknown
    # 4 structures of 12 bytes:
    # type0   =  pkm[32:44]
    # type1   =  pkm[44:56]
    # type2   =  pkm[56:68]
    # type3   =  pkm[68:80]
    trainer = {'id': trainerId,'name': trainerName, 'cname': cTrainerName}
    key = xor(trainer['id'], personality)
    
    type0, type1, type2, type3 = getTypes(pkm, personality)
    type0 = decryptTypes(type0, key)
    type1 = decryptTypes(type1, key)  # No changes between versions
    type2 = decryptTypes(type2, key)  # No changes between versions
    type3 = decryptTypes(type3, key)


    nPkmn  = struct.unpack('<H', type0[0:2])[0]&0x7ff
    pp = type1[8]
    attev = type2[1]
    metlevel = struct.unpack('<H', type3[2:4])[0]
    metlevel = metlevel&0x7f
    a = (trainerId & 0xFFFF0000) >> 16
    b = (trainerId & 0xFFFF)
    c = (personality & 0xFFFF0000) >> 16
    d = (personality & 0xFFFF)
    if (a^b^c^d)<SHINY_ODDS:  # This code is only valid for 1.3.2. TODO: Adapt for the new struct
        shiny=True
    else:
        shiny=False
    d = {
        'personality': personality,
        'trainer':     trainer,
        'nPkmn':    nPkmn,
        'pkmnName':    pkmnName,
        'cPkmnName':   cPkmnName,
        'lang': lang,
        'hiddenNatureModifier':hiddenNatureModifier,
        'EggSpecies': EggSpecies,
        'markings': markings,
        'shiny': shiny,
        'checksum': checksum,
        'unknown': unknown,        
        'version': version,
        'type0': type0,
        'type1': type1,
        'type2': type2,
        'type3': type3,
        'key': key,
    }
    return d

def serializeMon(mon, version, newOtId=None):
    """
    Given a pokemon representation, return the associated bytearray for the version
    """
    ba = bytearray(80)
    if newOtId:
        mon['key'] = mon['key'] ^ mon['trainer']['id'] ^ newOtId
        mon['trainer']['id'] = newOtId
    ba[0:4] = struct.pack('<I', mon['personality'])
    ba[4:8] = struct.pack('<I', newOtId)
    ba[8:18] = mon['cPkmnName']
    ba[18] = mon['lang']
    ba[19] = mon['EggSpecies']
    ba[20:27] = mon['trainer']['cname'][:7]
    ba[27] = mon['markings']
    ba[28:30] = struct.pack('<H', mon['checksum'])
    ba[30:32] = struct.pack('<H', mon['unknown'])

    if version == 2 and mon['version']==1:
        # The type0 and type3 (shiny) struct has been modified with the latest update
        species     = struct.unpack('<H', mon['type0'][0:2])[0]
        if species > NPOKEMON_V1:
            species += NPOKEMON_V2-NPOKEMON_V1
        # heldItem    = struct.unpack('<H', mon['type0'][2:4])[0]
        heldItem    = 0 # The item id does not match between 1.3.2 and 2.0
        experience  = struct.unpack('<I', mon['type0'][4:8])[0]
        mon['type0'][0:4]    = struct.pack('<I', (species&0x7ff)|(heldItem<<11))
        shinyOtherFlags      = struct.unpack('<I', mon['type3'][8:12])[0]
        if mon['shiny']:
            shinyOtherFlags |= 1
        mon['type3'][8:12]  = struct.pack('<I', shinyOtherFlags)

    ba = setTypes(ba, [mon['type0'],mon['type1'],mon['type2'],mon['type3']], mon['personality'])
    nchecksum = calculateChecksumBox(ba[32:32+48], 48)
    ba[28:30] = struct.pack('<H', nchecksum)
    ba[32:44] = decryptTypes(ba[32:44], mon['key'])
    ba[44:56] = decryptTypes(ba[44:56], mon['key'])
    ba[56:68] = decryptTypes(ba[56:68], mon['key'])
    ba[68:80] = decryptTypes(ba[68:80], mon['key'])
    return ba


###
# 2. Pokedex routines
def pokedexBitmaskToData(bmSeen, bmCaught, version):
    """
    Convert the bytearrays "bmSeen/PokedexFlags1" and "bmCaught/PokedexFlags2" to an array where:
    - 0 will indicate that the Pokemon hasn't been seen
    - 1 will indicate that the Pokemon has been seen
    - 2 will indicate that the Pokemon has been caught
    """
    nseen = 0
    ncaught = 0
    if version == 1:
        pokedex = [0]*len(bmSeen*8)
        for i in range(len(bmSeen)):
            for j in range(8):
                m = 1<<j
                if bmSeen[i]&m != 0:
                    pokedex[i*8+j]  = 1
                    nseen+=1
                if bmCaught[i]&m != 0:
                    pokedex[i*8+j]  = 2
                    ncaught+=1
    else:
        pokedex = [0]*(len(bmSeen)+len(bmCaught)*8)
        for i in range(len(bmSeen)):
            for j in range(8):
                m = 0x1<<j
                c1 = (bmSeen[i] & m)>>j
                c2 = (bmCaught[i] & m)>>j
                c2 <<= 1
                if c2:
                    pokedex[i*8+j] = 2
                    nseen+=1
                    ncaught+=1
                elif c1:
                    pokedex[i*8+j] = 1
                    nseen+=1
    #print(f"   Pokedex: seen - {nseen}; caught: {ncaught}")
    return pokedex


def pokedexDataToBitmask(pokedex, pokemons, baSeen, baCaught, version):
    """
    The complementary operation to pokedexBitmaskToData.

    However there is a "fix" because in the version 2.0, the shinies are represented by:
    - Bit to 1 in the baSeen bitmask and Bit to 1 in the baCaught bitmask
    In the serialization we did not take into account the possibility of shinies (as its representation is 
    different between version 1 and 2), so the second argument is a list of pokemons so we can identify which
    ones are shinies
    """
    if version == 1:
        # Not implemented the merge to version 1
        return baSeen, baCaught
    else:
        baSeen[0]  =0 # The first element of the bitmask is not used. The first species is 1
        baCaught[0]=0
        genPkmn = NPOKEMON_V1 # Up to gen8
        for i in range(1,genPkmn+1):
            candPkmn = pokedex[i-1]
            if i<=genPkmn:
                if candPkmn == 1:
                    baSeen[i//8] |= 1<<(i%8)
                elif candPkmn == 2:
                    baCaught[i//8] |= 1<<(i%8)
        for p in pokemons: # baSeen+baCaught => caught a shiny version
            if p['data']['shiny'] and p['data']['nPkmn']<=genPkmn:
                i = p['data']['nPkmn']
                baSeen[i//8] |= 1<<(i%8)
                baCaught[i//8] |= 1<<(i%8)
    return baSeen, baCaught


###
# 3. Item routines
def bagItemsToVersion2(il):
    """
    Given a list of objects (array of dicts in the form {id, quantity}), return a filtered list
    that can be injected to a 2.0 sav file format
    """
    ## The items must be sorted by the pocket they are located. Otherwise they are not copied.
    ## At the current moment only the *pokeballs* and *general items/medicines* are being copied
    ## Pokeball pocket
    FIRST_BALL_V2 = 1
    LAST_BALL_V2  = 28
    FIRST_BALL_V1 = 1
    LAST_BALL_V1  = 27

    ## Items pocket
    FIRST_MEDICINE_V2 = 39
    LAST_MEDICINE_V2  = 67
    LAST_EVOLUTION_V2  = 256
    FIRST_MEDICINE_V1 = 28
    LAST_MEDICINE_V1  = 56

    ## Berries pocket
    FIRST_BERRY_V2 = 525
    LAST_BERRY_V2  = 592
    FIRST_BERRY_V1 = 514
    LAST_BERRY_V1  = 581
    ## TMHM Pocket
    FIRST_TMHM_V2 = 593
    LAST_TMHM_V2  = 700
    FIRST_TMHM_V1 = 582
    LAST_TMHM_V1  = 689

    for el in il:
        if el['id']>LAST_BALL_V1:
            el['id']+=11
    sorted_array = sorted(il, key=lambda x: x['id'])
    filtered_array = []
    # Items pocket
    filtered_array += [d for d in sorted_array if (d['id']>LAST_BALL_V2 and d['id'] <= LAST_EVOLUTION_V2)]
    # Pokeball pocket
    filtered_array += [d for d in sorted_array if (d['id']<=LAST_BALL_V2)]
    # TMHM pocket
    # filtered_array += [d for d in sorted_array if (d['id']>=FIRST_TMHM_V2 and d['id'] <= LAST_TMHM_V2)]
    return filtered_array




##################################
# Main functions of this project #
##################################
def processObjects(sectors, tamperObject = None):
    """
    Given the saved sectors of a .sav file (output of the function processSavedSector), 
    return a dict with the basic information.

    This routine will return the following fields

    {
        stats -> hours, minutes, money
        pkmns
        pokedex
        items
        trainer -> name, id
        key -> encryption key for the "secured" blocks
    }

    The tamperObject will modify the returned variable with the injected fields. The options are not well documented but include
    fields like:

        money
        items
        cloneFirstinParty
        pkmn
        fullPokedex
        pokedex
        hours
        minutes

    It is not difficult to understand each member (I hope)
    """
    rogue13version = struct.unpack('<H', sectors['SLOT1_SAVEBLOCK1']['data'][ROGUESAVEVERSION_OFFSET:ROGUESAVEVERSION_OFFSET+2])[0]
    if rogue13version == 4:
        saveFormat = 1 # 1.3.2 and previous versions
        print("--- Detected a 1.3.2 save format ---")
        if SECTOR_DATA_SIZE != SECTOR_DATA_SIZE_V1:
            return None
    else:
        saveFormat = 2
        print("--- Detected a 2.0 save format ---")
        if SECTOR_DATA_SIZE != SECTOR_DATA_SIZE_V2:
            return None
    if tamperObject:
        tamperObject['lastInsertedItem'] = 0
        tamperObject['lastInsertedPkmn'] = 0
    objs = {'version': saveFormat}
    
    encryptionKey = 0
    dataSb1 = sectors['SLOT1_SAVEBLOCK1']['data']
    dataSb2 = sectors['SLOT1_SAVEBLOCK2']['data']
    dataPkmnStor = sectors['SLOT1_PKMNSTORAGE']['data']
    ##
    # Let's parse -> "SLOT1_SAVEBLOCK2":
    structOffset  = 0
    trainerName   = dataSb2[structOffset:structOffset + PLAYER_NAME_LENGTH + 1]; structOffset+=PLAYER_NAME_LENGTH + 1
    trainerGender = dataSb2[structOffset] & 0x1; structOffset += 1
    structOffset += 1 #specialSaveWarpFlags
    trainerId     = struct.unpack('<I', dataSb2[structOffset:structOffset + TRAINER_ID_LENGTH])[0]; structOffset+=4
    hours         = struct.unpack('<H', dataSb2[structOffset:structOffset + 2])[0]; 
    if tamperObject and 'hours' in tamperObject:
        hours = tamperObject['hours']
        dataSb2[structOffset:structOffset + 2] = struct.pack('<H', hours); 
    structOffset+=2
    minutes       = dataSb2[structOffset]; 
    if tamperObject and 'minutes' in tamperObject:
        hours = tamperObject['minutes']
        dataSb2[structOffset] = minutes; 
    structOffset+=1
    encryptionKey = struct.unpack('<I', dataSb2[ENCRIPTIONKEY_OFFSET:ENCRIPTIONKEY_OFFSET + 4])[0]
    money         = xor(encryptionKey, struct.unpack('<I', dataSb1[MONEY_OFFSET:MONEY_OFFSET + 4])[0])


    ##
    # Let's parse -> "SLOT1_SAVEBLOCK1":
    playerPartyCount = dataSb1[PLAYERPARTY_COUNTOFFSET] # Offset obtained from the spec for emerald rogue (global.h:238)
    objs['pkmns'] = []
    for i in range(playerPartyCount):
        # objs['pkmns'].append(bytearray(dataSb1[FIRSTPKMN_OFFSET+i*PKMN_STRUCT_SIZE:FIRSTPKMN_OFFSET+(i+1)*PKMN_STRUCT_SIZE]))
        objs['pkmns'].append({
            'data': createMon(bytearray(dataSb1[FIRSTPKMN_OFFSET+i*PKMN_STRUCT_SIZE:FIRSTPKMN_OFFSET+(i+1)*PKMNBOX_STRUCT_SIZE]), objs['version']),
            'box': 0,
            'pos': i+1
        })
    for i in range(TOTAL_BOXES):
        for j in range(PKMN_PER_BOX):
            offset = FIRSTPKMN_IN_BOX_OFFSET + (i*PKMN_PER_BOX+j)*PKMNBOX_STRUCT_SIZE
            otId = struct.unpack('<I',dataPkmnStor[offset + 4 : offset + 8])[0]
            if otId!=0 and otId !=0xFFFFFFFF: # otId!=0. It comes after the personality
                objs['pkmns'].append({
                    'data': createMon(bytearray(dataPkmnStor[offset : offset+PKMNBOX_STRUCT_SIZE]), objs['version']),
                    'box': i+1,
                    'pos': j+1
                })
            elif tamperObject and tamperObject['cloneFirstinParty'] and tamperObject['lastInsertedPkmn'] == 0:
                objs['pkmns'].append({
                    'data': objs['pkmns'][0]['data'],
                    'box': i+1,
                    'pos': j+1
                })
                dataPkmnStor[offset : offset+PKMNBOX_STRUCT_SIZE] = serializeMon(objs['pkmns'][0]['data'], objs['version'], trainerId)
                tamperObject['cloneFirstinParty']=False
            elif tamperObject and len(tamperObject['pkmn'])>tamperObject['lastInsertedPkmn']:
                objs['pkmns'].append({
                    'data': tamperObject['pkmn'][tamperObject['lastInsertedPkmn']],
                    'box': i+1,
                    'pos': j+1
                })
                dataPkmnStor[offset : offset+PKMNBOX_STRUCT_SIZE] = serializeMon(tamperObject['pkmn'][tamperObject['lastInsertedPkmn']], objs['version'], trainerId)
                tamperObject['lastInsertedPkmn']+=1
    ## tamper -> modify the money
    if tamperObject and tamperObject['money']>0:
        dataSb1[MONEY_OFFSET:MONEY_OFFSET+4] = struct.pack('<I', xor(encryptionKey, tamperObject['money']))
        money = tamperObject['money']
    objs['items']=[]
    for i in range(BAG_ITEM_CAPACITY):
        ## tamper -> items
        if tamperObject:
            if tamperObject['lastInsertedItem']<len(tamperObject['items']):
                dataSb1[ITEMS_OFFSET+i*4:ITEMS_OFFSET+i*4+2]   = struct.pack('<H', tamperObject['items'][tamperObject['lastInsertedItem']]['id'])
                dataSb1[ITEMS_OFFSET+i*4+2:ITEMS_OFFSET+i*4+4] = struct.pack('<H', xor(encryptionKey, tamperObject['items'][tamperObject['lastInsertedItem']]['quantity'])&0xffff)
                objs['items'].append({'id':tamperObject['items'][tamperObject['lastInsertedItem']]['id'],'quantity':tamperObject['items'][tamperObject['lastInsertedItem']]['quantity']})
                tamperObject['lastInsertedItem']+=1
            else:
                itemId = 0
                itemQuantity = 0
                dataSb1[ITEMS_OFFSET+i*4:ITEMS_OFFSET+i*4+2] = struct.pack('<H', itemId)
                dataSb1[ITEMS_OFFSET+i*4+2:ITEMS_OFFSET+i*4+4] = struct.pack('<H', itemQuantity)
        else:
            itemId = struct.unpack('<H', dataSb1[ITEMS_OFFSET+i*4:ITEMS_OFFSET+i*4+2])[0]
            itemQuantity = xor(struct.unpack('<H', dataSb1[ITEMS_OFFSET+i*4+2:ITEMS_OFFSET+i*4+4])[0], encryptionKey&0xffff)
            if itemId!=0:
                objs['items'].append({'id':itemId,'quantity':itemQuantity})
    # Tamper the pokedex
    if tamperObject and tamperObject['fullPokedex']:
        for i in range(DEXSIZE):
            dataSb1[DEXSEEN_OFFSET+i]=0xff
            dataSb1[DEXCAUGHT_OFFSET+i]=0xff
    if tamperObject and 'pokedex' in tamperObject:
        if saveFormat==2:
            dataSb1[DEXSEEN_OFFSET:DEXSEEN_OFFSET+DEXSIZE], dataSb1[DEXCAUGHT_OFFSET:DEXCAUGHT_OFFSET+DEXSIZE] = pokedexDataToBitmask(
                tamperObject['pokedex'],
                objs['pkmns'],
                dataSb1[DEXSEEN_OFFSET:DEXSEEN_OFFSET+DEXSIZE],
                dataSb1[DEXCAUGHT_OFFSET:DEXCAUGHT_OFFSET+DEXSIZE],
                saveFormat)
    objs['pokedex'] = pokedexBitmaskToData( dataSb1[DEXSEEN_OFFSET:DEXSEEN_OFFSET+DEXSIZE], dataSb1[DEXCAUGHT_OFFSET:DEXCAUGHT_OFFSET+DEXSIZE], saveFormat)
    objs['trainer'] = {
        'name':decodeString(trainerName),
        'id':trainerId,
        'gender':trainerGender
    }
    objs['stats'] = {
        'hours':hours,
        'minutes':minutes,
        'money':money,
    }
    objs['key'] = encryptionKey
    return objs

def printObjects(obj):
    """
    Print the output of processObjects to stdout
    """
    print(f"   Version:        {obj['version']} (1 = Previous to 2.0; 2 for the newest versions 2.0, 2.0.1...)")
    print(f"   Trainer Name:   {obj['trainer']['name']} (Gender: {obj['trainer']['gender']}; MALE=0, FEMALE=1)")
    print(f"   Trainer Id:     0x{obj['trainer']['id']:04X}")
    print(f"   Played Time:    {obj['stats']['hours']:02}:{obj['stats']['minutes']:02}")
    print(f"   Money:          {obj['stats']['money']}")
    print(f"   Encryption key: 0x{obj['key']}")
    print(f"   Items:          {len(obj['items'])}")
    for it in obj['items']:
        print("     "+str(it))
    print(f"   Pokemons:       {len(obj['pkmns'])}")
    for pkmn in obj['pkmns']:
        printMon(pkmn)
    print()


def processSavFile(savfile, tamperObject=None):
    """
    This routine process a .sav given its path
    """
    ##
    # Try to process the elements as a .sav of the version 1.3.2
    prepareGlobalsForVersion(1)
    sectors = processSavedSector(savfile)
    objs = processObjects(sectors, tamperObject)
    if objs==None: # If there is an error, try again but with the slot format for the 2.0.X game 
        prepareGlobalsForVersion(2)
        sectors = processSavedSector(savfile)
        objs = processObjects(sectors, tamperObject)
    return sectors, objs



################
# Main routine #
################
def main():
    """
    Examples
    1. Print the elements of a .sav file of a game in the 2.0 version
        python pokeemerald-rogue_savconverter.py Emerald\ Rogue_2_0.sav
    2. Print the elements of a .sav file of a game in the 1.3.2 version
        python pokeemerald-rogue_savconverter.py Emerald\ Rogue_1_3_2.sav
    3. Merge the pokemon, pokedex, money and items of a 1.3.2 .sav with a 2.0 one in the output file
        python pokeemerald-rogue_savconverter.py Emerald\ Rogue_2_0.sav -m Emerald\ Rogue_1_3_2a.sav -o Emerald\ Rogue_2_0_merged.sav


        Emerald\ Rogue_2_0.sav + Emerald\ Rogue_1_3_2a.sav => Emerald\ Rogue_2_0_merged.sav
    """
    ##
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Read and print fields from a binary save sector file.')
    parser.add_argument('input_file', help='The input binary file')
    parser.add_argument('-o', '--output-file', nargs='?', default=None, help='The output .sav file')
    parser.add_argument('-m', '--merge', nargs='?', default=None, help='Merge the content of this file into the input_file')  # on/off flag
    parser.add_argument('-t', '--tamper',action='store_true', help='Increment the money of the user/Full Pokedex/Testing purposes')  # on/off flag
    ##
    # Parse the arguments
    args = parser.parse_args()
    backupFileIfNeeded(args.input_file, args.input_file+".bak")
    if args.tamper:
        tamperObject = {
            'version': 1,
            'money':   99999,
            'items':   [{'id':4,'quantity':20}],
            'cloneFirstinParty': True,
            'pkmn': [],
            'fullPokedex': True,
        }
    else:
        tamperObject = None
    
    if args.merge:
        _, objs = processSavFile(args.merge)
        tamperObject = {
            'version': objs['version'],
            'money':   objs['stats']['money'],
            'hours':   objs['stats']['hours'],
            'minutes': objs['stats']['minutes'],
            'items':   bagItemsToVersion2(objs['items']),
            'cloneFirstinParty': False,
            'pkmn': [a['data'] for a in objs['pkmns']],
            'fullPokedex': False,
            'pokedex': objs['pokedex'],
        }
    ##
    #
    sectors, objs = processSavFile(args.input_file, tamperObject)
    printObjects(objs)
    if args.output_file:
        saveSectors(sectors,args.output_file)
    # Read and process the save sector
    # try:
    #     processSavedSector(args.input_file)
    # except:
    #     print("Error reading the block")

if __name__ == '__main__':
    main()
