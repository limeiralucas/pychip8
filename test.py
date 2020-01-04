import curses
import binascii
from time import sleep

sprites = [
    # 0
    0xf0,
    0x90,
    0x90,
    0x90,
    0xf0,

    # 1
    0x20,
    0x60,
    0x20,
    0x20,
    0x70,

    # 2
    0xf0,
    0x10,
    0xf0,
    0x80,
    0xf0,

    # 3
    0xf0,
    0x10,
    0xf0,
    0x10,
    0xf0,

    # 4
    0x90,
    0x90,
    0xf0,
    0x10,
    0x10,

    # 5
    0xf0,
    0x80,
    0xf0,
    0x10,
    0xf0,

    # 6
    0xf0,
    0x80,
    0xf0,
    0x90,
    0xf0,

    # 7
    0xf0,
    0x10,
    0x20,
    0x40,
    0x40,

    # 8
    0xf0,
    0x90,
    0xf0,
    0x90,
    0xf0,

    # 9
    0xf0,
    0x90,
    0xf0,
    0x10,
    0xf0,

    # A
    0xf0,
    0x90,
    0xf0,
    0x90,
    0x90,

    # B
    0xe0,
    0x90,
    0xe0,
    0x90,
    0xe0,

    # C
    0xf0,
    0x80,
    0x80,
    0x80,
    0xf0,

    # D
    0xe0,
    0x90,
    0x90,
    0x90,
    0xe0,

    # E
    0xf0,
    0x80,
    0xf0,
    0x80,
    0xf0,

    # F
    0xf0,
    0x80,
    0xf0,
    0x80,
    0x80
]

def append_hex(a, b):
    sizeof_b = 0

    # get size of b in bits
    while((b >> sizeof_b) > 0):
        sizeof_b += 1

    # align answer to nearest 4 bits (hex digit)
    sizeof_b += sizeof_b % 4

    return (a << sizeof_b) | b

def run(stdscr):
    filepath = 'tetris.ch8'
    ram = [0] * 4096
    ram.extend(sprites)
    counter = 0x200
    with open(filepath, 'rb') as file:
        byte = file.read(1)
        while byte:
            num = int(binascii.hexlify(byte), 16)
            ram[counter] = num
            byte = file.read(1)
            counter += 1
    v = [0] * 16
    vi = 0
    vd = 0
    vt = 0
    pc = 0x200
    sp = 0x0
    stack = [0] * 16
    screen = [[0] * 64] * 32

    while True:
        not_implemented = False
        actual_pc = pc
        inst0 = ram[pc]
        inst1 = ram[pc + 1]
        inst = [
            inst0 >> 4,
            inst0 & 0xf,
            inst1 >> 4,
            inst1 & 0xf,
        ]
        y = inst[2]
        x = inst[1]
        nnn = (((inst[1] << 4) + inst[2]) << 4) + inst[3]
        kk = (inst[2] << 4) + inst[3]
        n = inst[3]

        if(inst[0] == 0):
            if(inst[1] == 0 and inst[2] == 0xe):
                if(inst[3] == 0):
                    # 00E0 - CLS
                    stdscr.clear()
                elif(inst[3] == 0xe):
                    # 00EE - RET
                    pc = stack[sp]
                    sp -= 1

        elif(inst[0] == 1):
            # 1nnn - JP addr
            pc = nnn

        elif(inst[0] == 2):
            # 2nnn - CALL addr
            sp += 1
            stack[sp] = pc
            pc = nnn - 2

        elif(inst[0] == 3):
            # 3xkk - SE Vx, byte
            if(v[x] == kk):
                pc += 2

        elif(inst[0] == 4):
            # 4xkk - SNE Vx, byte
            if(v[x] != kk):
                pc += 2

        elif(inst[0] == 5 and inst[3] == 0):
            # 5xy0 - SE Vx, Vy
            if(v[x] == vy):
                pc += 2

        elif(inst[0] == 6):
            # 6xkk - LD Vx, byte
            v[x] = kk

        elif(inst[0] == 7):
            # 7xkk - ADD Vx, byte
            v[x] = v[x] + kk

        elif(inst[0] == 8):
            if(inst[3] == 0):
                # 8xy0 - LD Vx, Vy
                v[x] = v[y]
            elif(inst[3] == 1):
                # 8xy1 - OR Vx, Vy
                v[x] = v[x] | v[y]
            elif(inst[3] == 2):
                # 8xy2 - AND Vx, Vy
                v[x] = v[x] & v[y]
            elif(inst[3] == 3):
                # 8xy3 - XOR Vx, Vy
                v[x] = v[x] ^ v[y]
            elif(inst[3] == 4):
                # 8xy4 - ADD Vx, Vy
                result = v[x] + v[y]
                v[0xf] = 1 if result > 255 else 0
                v[x] = result & 0xff
            elif(inst[3] == 5):
                # 8xy5 - SUB Vx, Vy
                result = v[y] - v[x]
                v[0xf] = 1 if v[x] > v[y] else 0
                v[x] = result if result >= 0 else 0
            elif(inst[3] == 6):
                # Set Vx = Vx SHR 1
                not_implemented = True
            elif(inst[3] == 7):
                # 8xy7 - SUBN Vx, Vy
                not_implemented = True
            elif(inst[3] == 8):
                # 8xyE - SHL Vx {, Vy}
                not_implemented = True

        elif(inst[0] == 9):
            # 9xy0 - SNE Vx, Vy
            if(v[x] != v[y]):
                pc += 2

        elif(inst[0] == 0xa):
            # Annn - LD I, addr
            vi = nnn

        elif(inst[0] == 0xb):
            # Bnnn - JP V0, addr
            pc = nnn + v[0] - 2

        elif(inst[0] == 0xc):
            # Cxkk - RND Vx, byte
            v[x] = 255 & kk

        elif(inst[0] == 0xd):
            # Dxyn - DRW Vx, Vy, nibble
            start = vi
            x = 0
            while(x < n):
                s = ram[start + x]
                values = [
                    s & 0x80,
                    s & 0x64,
                    s & 0x20,
                    s & 0x10
                ]

                for column in range(4):
                    screen[v[x] + column][v[y] + x] = values[column]
                x += 1
        else:
            not_implemented = True

        pc += 2
        stdscr.clear()
        info = '{}: {} {} {} {} ({})'.format(
            hex(actual_pc),
            hex(inst[0]),
            hex(inst[1]),
            hex(inst[2]),
            hex(inst[3]),
            not_implemented
        )

        for nline, line in enumerate(screen):
            for ncolumn, column in enumerate(line):
                stdscr.addstr(nline, ncolumn, '■' if column != 0 else ' ')

        stdscr.addstr(34, 0, info)
        stdscr.refresh()
        # sleep(0.0165)
        sleep(0.2)


if __name__ == '__main__':
    curses.wrapper(run)
