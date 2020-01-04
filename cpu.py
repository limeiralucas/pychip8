from random import randint


class Chip8CPU(object):
    def __init__(self, screen):
        self.operand = 0
        self.screen = screen
        self.memory = bytearray(4096)

        # Delay and Sound timers
        self.timers = {
            'delay': 0,
            'sound': 0,
        }

        # Registers
        self.registers = {
            'v': [],
            'index': 0,
            'sp': 0,
            'pc': 0,
        }

        self.stack = []

        # Operations Lookup
        self.operations = {
            0x0: self.clear_return,
            0x1: self.jump_to_location,
            0x2: self.call_subroutine,
            0x3: self.skip_instruction,
            0x4: self.skip_instruction,
            0x5: self.skip_instruction,
            0x6: self.set_register,
            0x7: self.add_to_register,
            0x8: self.execute_logical_operation,
            0x9: self.skip_instruction,
            0xA: self.set_index,
            0xB: self.jump_to_location_plus_v0,
            0xC: self.rand_vx,
            0xD: self.draw_sprite,
            0xF: self.execute_misc_operation,
        }

        # Logical operations lookup
        self.logical_operation_lookup = {
            0x0: self.load_vy_into_vx,
            0x1: self.load_or_vy_into_vx,
            0x2: self.load_and_vy_into_vx,
            0x3: self.load_xor_vy_into_vx,
            0x4: self.add_vy_to_vx,
            0x5: self.subtract_vy_from_vx,
            0x6: self.shr_vx,
            0x7: self.subtract_vx_from_vy,
            0x8: self.shl_vx,
        }

        # Misc operations lookup
        self.misc_operation_lookup = {
            0x15: self.set_delay_timer,
            0x1E: self.add_vx_to_index,
        }

        self.reset()

    # Reset CPU
    def reset(self):
        self.registers['v'] = [0] * 16
        self.registers['pc'] = 0x0200
        self.registers['sp'] = 0
        self.registers['index'] = 0

        self.timers['delay'] = 0
        self.timers['sound'] = 0

        self.stack = [0] * 16

    # Load ROM File into memory
    def load_rom(self, filename, offset=0x200):
        with open(filename, 'rb') as file:
            data = file.read()
            for index, val in enumerate(data):
                self.memory[offset + index] = val

    # Load Fontset
    def load_font(self, font):
        for index, data in enumerate(font):
            self.memory[index] = data

    # Execute Instruction base on most significant byte
    def execute_instruction(self):
        self.operand = int(self.memory[self.registers['pc']])
        self.operand = self.operand << 8
        self.operand += int(self.memory[self.registers['pc'] + 1])
        self.registers['pc'] += 2

        operation = (self.operand & 0xF000) >> 12
        try:
            v_debug = {'v[%s]' % index: hex(
                value) for index, value in enumerate(self.registers['v'])}
            stack_debug = {'s[%s]' % index: hex(
                value) for index, value in enumerate(self.stack)}
            debug_info = {
                'pc': hex(self.registers['pc']),
                'v': v_debug,
                'stack': stack_debug,
                'index': hex(self.registers['index']),
                'sp': hex(self.registers['sp']),
                'operand': '%s (%s)' % (hex(self.operand), hex(operation)),
                'sprite': bin(self.memory[self.registers['index']]),
            }
            self.screen.update_debug_info(debug_info)
            self.operations[operation]()
        except KeyError:
            self.screen.update_debug_info({
                'pc': '%s (Operation not implemented [%s])' % (hex(self.registers['pc']), hex(self.operand))
            })

    # Operations
    def clear_return(self):
        operation = self.operand & 0x00FF

        if operation == 0x00E0:
            self.clear()

        elif operation == 0x00EE:
            self.return_from_subroutine()

    # Misc operations seek and execution
    def execute_misc_operation(self):
        sub_operation = self.operand & 0x00FF
        self.misc_operation_lookup[sub_operation]()

    # Logical operations seek and execution
    def execute_logical_operation(self):
        sub_operation = self.operand & 0x000F
        self.logical_operation_lookup[sub_operation]()

    # Clear Screen
    # 00E0 - CLS
    def clear(self):
        self.screen.clear()

    # Return from subroutine
    # 00EE - RET
    def return_from_subroutine(self):
        self.registers['pc'] = self.stack[self.registers['sp']]
        self.registers['sp'] -= 1

    # Jump to location
    # 1nnn - JP addr
    def jump_to_location(self, address=None):
        addr = address if address else self.operand & 0x0FFF
        self.registers['pc'] = addr

    # Call subroutine
    # 2nnn - CALL addr
    def call_subroutine(self):
        self.registers['sp'] += 1
        self.stack[self.registers['sp']] = self.registers['pc']
        address = (self.operand & 0x0FFF)
        self.jump_to_location(address)

    # Skip instruction based on operation
    def skip_instruction(self):
        sub_operation = self.operand & 0xF000
        x = (self.operand & 0x0F00) >> 8
        y = (self.operand & 0x00F0) >> 4
        kk = self.operand & 0x00FF

        should_skip = False

        # 3xkk - SE Vx, byte
        if sub_operation == 0x3000:
            should_skip = self.registers['v'][x] == kk

        # 4xkk - SNE Vx, byte
        elif sub_operation == 0x4000:
            should_skip = self.registers['v'][x] != kk

        # 5xy0 - SE Vx, Vy
        elif sub_operation == 0x5000:
            should_skip = self.registers['v'][x] == self.registers['v'][y]

        # 9xy0 - SNE Vx, Vy
        elif sub_operation == 0x9000:
            should_skip = self.registers['v'][x] != self.registers['v'][y]

        self.registers['pc'] += 2 if should_skip else 0

    # Set register to value
    # 6xkk - LD Vx, byte
    def set_register(self, value=None):
        x = (self.operand & 0x0F00) >> 8
        value_to_set = value if value else (self.operand & 0x00FF)

        self.registers['v'][x] = value_to_set

    # Add value to register
    # 7xkk - ADD Vx, byte
    def add_to_register(self, value=None):
        x = (self.operand & 0x0F00) >> 8
        value_to_add = value if value else (self.operand & 0x00FF)
        result = self.registers['v'][x] + value_to_add

        if result > 255:
            self.registers['v'][0xF] = self.registers['v'][0xF] | 1
            result = 0x000F & result
        else:
            self.registers['v'][0xF] = self.registers['v'][0xF] & 0

        self.registers['v'][x] = result

    # Subtract value from register
    def subtract_from_register(self, value=None, register_index=None):
        x = (self.operand & 0x0F00) >> 8
        reg_index = register_index if register_index else x
        value_to_subtract = value if value else (self.operand & 0x00FF)
        result = self.registers['v'][reg_index] - value_to_subtract

        if result < 0:
            self.registers['v'][0xF] = self.registers['v'][0xF] | 1
            result += 255
        else:
            self.registers['v'][0xF] = self.registers['v'][0xF] & 0

        self.registers['v'][x] = result

    # Load value of register vy into register vx
    # 8xy0 - LD Vx, Vy
    def load_vy_into_vx(self):
        y = (self.operand & 0x00F0) >> 4

        self.set_register(self.registers['v'][y])

    # Load value of vx OR vy into register vx
    # 8xy1 - OR Vx, Vy
    def load_or_vy_into_vx(self):
        y = (self.operand & 0x00F0) >> 4
        x = (self.operand & 0x0F00) >> 8
        value = self.registers['v'][x] | self.registers['v'][y]

        self.set_register(value)

    # Load value of vx AND vy into register vx
    # 8xy2 - AND Vx, Vy
    def load_and_vy_into_vx(self):
        y = (self.operand & 0x00F0) >> 4
        x = (self.operand & 0x0F00) >> 8
        value = self.registers['v'][x] & self.registers['v'][y]

        self.set_register(value)

    # Load value of vx XOR vy into register vx
    # 8xy3 - XOR Vx, Vy
    def load_xor_vy_into_vx(self):
        y = (self.operand & 0x00F0) >> 4
        x = (self.operand & 0x0F00) >> 8
        value = self.registers['v'][x] ^ self.registers['v'][y]

        self.set_register(value)

    # Adds value of vy to vx and stores the result into vx
    # 8xy4 - ADD Vx, Vy
    def add_vy_to_vx(self):
        y = (self.operand & 0x00F0) >> 4

        self.add_to_register(self.registers['v'][y])

    # Subtracts value of vy from vx and stores the result into vx
    # 8xy5 - SUB Vx, Vy
    def subtract_vy_from_vx(self):
        y = (self.operand & 0x00F0) >> 4

        self.subtract_from_register(self.registers['v'][y])

    # Divides the value of vx depending on its lsb
    # 8xy6 - SHR Vx {, Vy}
    def shr_vx(self):
        x = (self.operand & 0x0F00) >> 8
        vx_lsb = bin(self.registers['v'][x] & 0x000F)
        vx_lsb = int(vx_lsb[-1])

        if vx_lsb == 1:
            self.registers['v'][0xF] = self.registers['v'][0xF] | 1
        else:
            self.registers['v'][0xF] = self.registers['v'][0xF] & 0

        self.registers['v'][x] = self.registers['v'][x] // 2

    # Substracts the value of vx from vy and stores the result into vx
    # 8xy7 - SUBN Vx, Vy
    def subtract_vx_from_vy(self):
        y = (self.operand & 0x00F0) >> 4
        x = (self.operand & 0x0F00) >> 8

        self.subtract_from_register(self.registers['v'][x], y)

    # Multiplies the value of vx based on its msb
    # 8xyE - SHL Vx {, Vy}
    def shl_vx(self):
        x = (self.operand & 0x0F00) >> 8
        vx_msb = bin((self.registers['v'][x] & 0xF000) >> 12)
        vx_msb = int(vx_msb[0])

        if vx_msb == 1:
            self.registers['v'][0xF] = self.registers['v'][0xF] | 1
        else:
            self.registers['v'][0xF] = self.registers['v'][0xF] & 0

        self.registers['v'][x] = self.registers['v'][x] * 2

    # Set index register value
    # Annn - LD I, addr
    def set_index(self):
        value = self.operand & 0x0FFF

        self.registers['index'] = value

    # Jump to address plus value of register v0
    # Bnnn - JP V0, addr
    def jump_to_location_plus_v0(self):
        addr = (self.operand & 0x0FFF) + self.registers['v'][0]

        self.jump_to_location(addr)

    # Set delay timer
    # Fx15 - LD DT, Vx
    def set_delay_timer(self):
        x = (self.operand & 0x0F00) >> 8
        self.timers['delay'] = self.registers['v'][x]

    # Add value of register vx to index register
    # Fx1E - ADD I, Vx
    def add_vx_to_index(self):
        x = (self.operand & 0x0F00) >> 8
        self.registers['index'] += self.registers['v'][x]

    # Set random number to vx
    # Cxkk - RND Vx, byte
    def rand_vx(self):
        x = (self.operand & 0x0F00) >> 8
        self.registers['v'][x] = randint(0, 255)
    # Draw Sprite to Screen

    def draw_sprite(self):
        x_source = (self.operand & 0x0F00) >> 8
        y_source = (self.operand & 0x00F0) >> 4
        x_pos = self.registers['v'][x_source]
        y_pos = self.registers['v'][y_source]
        num_bytes = self.operand & 0x000F
        self.registers['v'][0xF] = 0

        self.draw_to_screen(x_pos, y_pos, num_bytes)

    # Draw to screen using screen interface
    def draw_to_screen(self, x_pos, y_pos, num_bytes):
        for y_index in range(num_bytes):
            pixel_line = bin(self.memory[self.registers['index'] + y_index])
            pixel_line = pixel_line[2:].zfill(8)
            y_coord = y_pos + y_index
            for x_index in range(8):
                x_coord = x_pos + x_index
                pixel = int(pixel_line[x_index])

                is_active = self.screen.get_pixel(x_coord, y_coord)
                if pixel == 1 and is_active == 1:
                    self.registers['v'][0xF] = self.registers['v'][0xF] | 1
                    pixel = 0

                elif pixel == 0 and is_active == 1:
                    pixel = 1

                self.screen.draw_pixel(x_coord, y_coord, pixel)
