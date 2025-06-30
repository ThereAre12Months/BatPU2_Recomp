from llvmlite import ir, binding
import os

class Instruction:
    NOP = 0x0
    HLT = 0x1
    ADD = 0x2
    SUB = 0x3
    NOR = 0x4
    AND = 0x5
    XOR = 0x6
    RSH = 0x7
    LDI = 0x8
    ADI = 0x9
    JMP = 0xa
    BRH = 0xb
    CAL = 0xc
    RET = 0xd
    LOD = 0xe
    STR = 0xf

    def __init__(self, pc, op, reg_a, reg_b, reg_c, off, imm, addr, cond) -> None:
        self.pc = pc
        self.op = op

        self.reg_a = reg_a
        self.reg_b = reg_b
        self.reg_c = reg_c

        self.off  = off
        self.imm  = imm
        self.addr = addr

        self.cond = cond

class Recompiler:
    def __init__(self, in_file:str, out_file:str, headless:bool=False) -> None:
        self.in_file  = in_file
        self.out_file = out_file
        self.headless = headless

        self.name = os.path.splitext(os.path.basename(self.in_file))[0]
        self.load_mc_file()

        self.init_llvm_binding()
        self.init_llvm_module()
        self.declare_helper_funcs()

    def recompile(self) -> None:
        self.init_llvm_builder()

        self.find_branch_targets()
        self.build_llvm_blocks()

        self.builder.position_at_end(self.exit_block)
        self.build_exit_routine()

        self.builder.position_at_end(self.error_block)
        self.build_error_routine()

        self.builder.position_at_end(self.entry)

        self.allocate_data()
        self.init_runtime()

        self.builder.branch(self.blocks[0])

        for instr in self.instructions:
            self.translate_instruction(instr)

        self.terminate_all_blocks()

        self.write_llvm_file()

    def translate_instruction(self, instr:Instruction):
        self.position_at_end_of_closest_block(instr.pc)

        match instr.op:
            case Instruction.NOP:
                ...
            case Instruction.HLT:
                self.instr_hlt()
            case Instruction.ADD:
                self.instr_add(instr.reg_a, instr.reg_b, instr.reg_c)
            case Instruction.SUB:
                self.instr_sub(instr.reg_a, instr.reg_b, instr.reg_c)
            case Instruction.NOR:
                self.instr_nor(instr.reg_a, instr.reg_b, instr.reg_c)
            case Instruction.AND:
                self.instr_and(instr.reg_a, instr.reg_b, instr.reg_c)
            case Instruction.XOR:
                self.instr_xor(instr.reg_a, instr.reg_b, instr.reg_c)
            case Instruction.RSH:
                self.instr_rsh(instr.reg_a, instr.reg_c)
            case Instruction.LDI:
                self.instr_ldi(instr.reg_a, instr.imm)
            case Instruction.ADI:
                self.instr_adi(instr.reg_a, instr.imm)
            case Instruction.JMP:
                self.instr_jmp(instr.addr)
            case Instruction.BRH:
                self.instr_brh(instr.cond, instr.addr, instr.pc+1)
            case Instruction.CAL:
                self.instr_cal(instr.pc, instr.addr)
            case Instruction.RET:
                self.instr_ret()
            case Instruction.LOD:
                self.instr_lod(instr.pc, instr.reg_a, instr.off, instr.reg_b)
            case Instruction.STR:
                self.instr_str(instr.pc, instr.reg_a, instr.off, instr.reg_b)
            case _:
                raise Exception(f"Instruction {instr.op:01x} not yet implemented")

    def init_llvm_binding(self) -> None:
        binding.initialize()
        binding.initialize_native_target()
        binding.initialize_native_asmprinter()

    def init_llvm_module(self) -> None:
        self.mod = ir.Module(self.name)
        self.mod.triple = binding.get_default_triple()

    def declare_helper_funcs(self) -> None:
        self.funcs = {
        "init_headless": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "init_headless",
        ),
        "deinit_headless": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "deinit_headless",
        ),
        "init": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "init",
        ),
        "deinit": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "deinit",
        ),
        "raise_error": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "raise_error",
        ),
        "draw_pixel": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8), ir.IntType(8)]),
            name   = "draw_pixel",
        ),
        "clear_pixel": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8), ir.IntType(8)]),
            name   = "clear_pixel",
        ),
        "get_pixel": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.IntType(8), [ir.IntType(8), ir.IntType(8)]),
            name   = "get_pixel",
        ),
        "update_screen": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "update_screen",
        ),
        "clear_screen": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "clear_screen",
        ),
        "push_char": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8)]),
            name   = "push_char",
        ),
        "clear_char_buffer": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "clear_char_buffer",
        ),
        "flush_char_buffer": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "flush_char_buffer",
        ),
        "set_num": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8)]),
            name   = "set_num",
        ),
        "set_signedness": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(1)]),
            name   = "set_signedness",
        ),
        "write_num": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "write_num",
        ),
        "get_controller": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.IntType(8), []),
            name   = "get_controller",
        ),
        "get_random_num": ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.IntType(8), []),
            name   = "get_random_num",
        ),
    }

    def load_mc_file(self) -> None:
        with open(self.in_file, "r") as code:
            lines = code.read().splitlines()

        self.instructions = []
        for pc, line in enumerate(lines):
            self.instructions.append(Instruction(
                pc = pc,
                op = int(line[:4], 2),

                reg_a = int(line[4 :8 ], 2),
                reg_b = int(line[8 :12], 2),
                reg_c = int(line[12:16], 2),

                off  = (int(line[12:16], 2) & 0x7) + bool(int(line[12:16], 2) & 0x8) * -8,
                imm  = int(line[8:16], 2),
                addr = int(line[6:16], 2),

                cond = int(line[4:6], 2),
            ))

    def write_llvm_file(self) -> None:
        with open(self.out_file, "w") as output:
            output.write(str(self.mod))

    def find_branch_targets(self) -> None:
        self.branch_targets = []
        self.return_targets = []

        for instr in self.instructions:
            if instr.op == Instruction.JMP:
                self.branch_targets.append(instr.addr)
                self.branch_targets.append(instr.pc + 1)

            elif instr.op == Instruction.BRH:
                self.branch_targets.append(instr.addr)
                self.branch_targets.append(instr.pc + 1)

            elif instr.op == Instruction.CAL:
                self.branch_targets.append(instr.addr)
                self.return_targets.append(instr.pc + 1)

            elif instr.op == Instruction.RET:
                # RET produces a block terminator, so a new block after it must be created
                self.branch_targets.append(instr.pc + 1)

            elif instr.op == Instruction.LOD:
                self.branch_targets.append(instr.pc + 1)

            elif instr.op == Instruction.STR:
                self.branch_targets.append(instr.pc + 1)

    def init_llvm_builder(self) -> None:
        main_func = ir.Function(
            module = self.mod,
            ftype  = ir.FunctionType(ir.IntType(32), []),
            name   = "main",
        )

        self.entry = main_func.append_basic_block(name = "entry")
        self.builder = ir.IRBuilder(self.entry)

    def build_llvm_blocks(self) -> None:
        self.exit_block  = self.builder.append_basic_block(name = "exit_block")
        self.error_block = self.builder.append_basic_block(name = "error_block")

        self.blocks = {}

        zero_block = self.builder.append_basic_block(name = f"block_{0:04x}")
        self.blocks.update({0: zero_block})

        # sorting the blocks isn't strictly necessary, but makes the emitted llvmir make more sense
        all_targets = sorted(list(set(self.branch_targets) | set(self.return_targets)))
        for target in all_targets:
            block = self.builder.append_basic_block(name = f"block_{target:04x}")
            self.blocks.update({target: block})

    def terminate_all_blocks(self) -> None:
        block_addrs = sorted(list(self.blocks.keys()))
        for idx in range(len(block_addrs)):
            if idx >= len(block_addrs) - 1:
                if not self.blocks[block_addrs[idx]].is_terminated:
                    self.builder.position_at_end(self.blocks[block_addrs[idx]])
                    self.builder.branch(self.exit_block)
            if not self.blocks[block_addrs[idx]].is_terminated:
                self.builder.position_at_end(self.blocks[block_addrs[idx]])
                self.builder.branch(self.blocks[block_addrs[idx+1]])

    def find_closest_block(self, target_addr):
        closest_addr  = 0
        closest_block = self.blocks[0]
        for addr, block in sorted(self.blocks.items(), key=lambda item: item[0]):
            if addr > target_addr:
                break

            closest_addr  = addr
            closest_block = block

        return closest_block

    def find_next_closest_block(self, target_addr):
        closest_addr = 0
        block_idx = 0
        block_addrs = list(self.blocks.keys())
        while block_idx < len(block_addrs):
            if block_addrs[block_idx] > target_addr:
                break

            block_idx += 1

        if block_idx == len(block_addrs) - 1:
            return self.exit_block

        return self.blocks[block_addrs[block_idx]]

    def position_at_end_of_closest_block(self, target_addr) -> None:
        closest_block = self.find_closest_block(target_addr)

        self.builder.position_at_end(closest_block)

    def allocate_data(self) -> None:
        self.ram   = self.builder.alloca(ir.IntType(8),  size=256, name="ram")
        self.stack = self.builder.alloca(ir.IntType(16), size=16,  name="stack")
        self.sp    = self.builder.alloca(ir.IntType(8),  name="sp")
        self.builder.store(ir.Constant(ir.IntType(8), 0), self.sp)

        self.regs = []
        for r_idx in range(16):
            reg = self.builder.alloca(ir.IntType(8), name=f"r{r_idx}")
            self.builder.store(
                ir.Constant(ir.IntType(8), 0),
                reg
            )
            self.regs.append(reg)

        self.flag_Z = self.builder.alloca(ir.IntType(1), name="flag_Z")
        self.flag_C = self.builder.alloca(ir.IntType(1), name="flag_C")
        self.builder.store(ir.Constant(ir.IntType(1), 0), self.flag_Z)
        self.builder.store(ir.Constant(ir.IntType(1), 0), self.flag_C)

        self.pixel_x = self.builder.alloca(ir.IntType(8), name="pixel_x")
        self.pixel_y = self.builder.alloca(ir.IntType(8), name="pixel_y")
        self.builder.store(ir.Constant(ir.IntType(8), 0), self.pixel_x)
        self.builder.store(ir.Constant(ir.IntType(8), 0), self.pixel_y)

    def init_runtime(self) -> None:
        if self.headless:
            self.builder.call(
                self.funcs["init_headless"],
                [],
            )

        else:
            self.builder.call(
                self.funcs["init"],
                [],
            )

    def build_exit_routine(self) -> None:
        if self.headless:
            self.builder.call(
                self.funcs["deinit_headless"],
                [],
            )
        else:
            self.builder.call(
                self.funcs["deinit"],
                [],
            )
        self.builder.ret(ir.Constant(ir.IntType(32), 0))

    def build_error_routine(self) -> None:
        self.builder.call(
            self.funcs["raise_error"],
            [],
        )
        self.builder.ret(ir.Constant(ir.IntType(32), 1))

    def instr_hlt(self) -> None:
        if self.headless:
            self.builder.call(
                self.funcs["deinit_headless"],
                [],
            )
        else:
            self.builder.call(
                self.funcs["deinit"],
                [],
            )

    def instr_add(self, ra, rb, rc) -> None:
        ra_val = self.builder.load(self.regs[ra])
        sum_ = self.builder.add(
            ra_val,
            self.builder.load(self.regs[rb])
        )

        if rc != 0:
            self.builder.store(
                sum_,
                self.regs[rc]
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                sum_,
                ir.Constant(ir.IntType(8), 0)
            ),
            self.flag_Z
        )
        self.builder.store(
            self.builder.icmp_unsigned(
                "<",
                sum_,
                ra_val,
            ),
            self.flag_C
        )

    def instr_sub(self, ra, rb, rc) -> None:
        ra_val = self.builder.load(self.regs[ra])
        diff = self.builder.sub(
            ra_val,
            self.builder.load(self.regs[rb])
        )

        if rc != 0:
            self.builder.store(
                diff,
                self.regs[rc],
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                diff,
                ir.Constant(ir.IntType(8), 0)
            ),
            self.flag_Z,
        )
        self.builder.store(
            self.builder.icmp_unsigned(
                "<=",
                diff,
                ra_val,
            ),
            self.flag_C
        )

    def instr_nor(self, ra, rb, rc) -> None:
        res = self.builder.not_(
            self.builder.or_(
                self.builder.load(self.regs[ra]),
                self.builder.load(self.regs[rb]),
            )
        )

        if rc != 0:
            self.builder.store(
                res,
                self.regs[rc]
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                res,
                ir.Constant(ir.IntType(8), 0),
            ),
            self.flag_Z
        )

    def instr_and(self, ra, rb, rc) -> None:
        res = self.builder.and_(
            self.builder.load(self.regs[ra]),
            self.builder.load(self.regs[rb]),
        )

        if rc != 0:
            self.builder.store(
                res,
                self.regs[rc],
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                res,
                ir.Constant(ir.IntType(8), 0),
            ),
            self.flag_Z
        )

    def instr_xor(self, ra, rb, rc) -> None:
        res = self.builder.xor(
            self.builder.load(self.regs[ra]),
            self.builder.load(self.regs[rb]),
        )

        if rc != 0:
            self.builder.store(
                res,
                self.regs[rc],
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                res,
                ir.Constant(ir.IntType(8), 0),
            ),
            self.flag_Z
        )

    def instr_rsh(self, ra, rc) -> None:
        res = self.builder.lshr(
            self.builder.load(self.regs[ra]),
            ir.Constant(ir.IntType(8), 1),
        )

        if rc != 0:
            self.builder.store(
                res,
                self.regs[rc],
            )

    def instr_ldi(self, reg, imm) -> None:
        if reg == 0:
            return

        self.builder.store(
            ir.Constant(ir.IntType(8), imm),
            self.regs[reg],
        )

    def instr_adi(self, reg, imm) -> None:
        reg_val = self.builder.load(self.regs[reg])
        res = self.builder.add(
            reg_val,
            ir.Constant(ir.IntType(8), imm),
        )

        if reg != 0:
            self.builder.store(
                res,
                self.regs[reg],
            )

        self.builder.store(
            self.builder.icmp_unsigned(
                "==",
                res,
                ir.Constant(ir.IntType(8), 0),
            ),
            self.flag_Z
        )

        self.builder.store(
            self.builder.icmp_unsigned(
                "<",
                res,
                reg_val,
            ),
            self.flag_C
        )

    def instr_jmp(self, addr) -> None:
        self.builder.branch(
            self.blocks[addr]
        )

    def instr_brh(self, cond, true_addr, false_addr) -> None:
        val = None
        if cond == 0:
            val = self.builder.icmp_unsigned(
                "==",
                self.builder.load(self.flag_Z),
                ir.Constant(ir.IntType(1), 1)
            )
        elif cond == 1:
            val = self.builder.icmp_unsigned(
                "!=",
                self.builder.load(self.flag_Z),
                ir.Constant(ir.IntType(1), 1)
            )
        elif cond == 2:
            val = self.builder.icmp_unsigned(
                "==",
                self.builder.load(self.flag_C),
                ir.Constant(ir.IntType(1), 1)
            )
        elif cond == 3:
            val = self.builder.icmp_unsigned(
                "!=",
                self.builder.load(self.flag_C),
                ir.Constant(ir.IntType(1), 1)
            )

        self.builder.cbranch(
            val,
            self.blocks[true_addr],
            self.blocks[false_addr],
        )

    def instr_cal(self, pc, addr) -> None:
        sp0 = self.builder.load(self.sp)
        elem_ptr = self.builder.gep(
            self.stack,
            [sp0],
        )
        self.builder.store(
            ir.Constant(ir.IntType(16), pc+1),
            elem_ptr,
        )
        self.builder.store(
            self.builder.add(
                sp0,
                ir.Constant(ir.IntType(8), 1),
            ),
            self.sp,
        )
        self.builder.branch(
            self.blocks[addr]
        )

    def instr_ret(self) -> None:
        new_sp = self.builder.sub(
            self.builder.load(self.sp),
            ir.Constant(ir.IntType(8), 1),
        )
        self.builder.store(
            new_sp,
            self.sp
        )
        elem_ptr = self.builder.gep(
            self.stack,
            [new_sp],
        )
        ret_addr = self.builder.load(elem_ptr)

        switch = self.builder.switch(
            ret_addr,
            self.error_block, # the return address should always be in self.return_targets
        )

        for ret_target in self.return_targets:
            switch.add_case(ir.Constant(ir.IntType(16), ret_target), self.blocks[ret_target])

    def instr_lod(self, pc, ra, off, rb) -> None:
        calc_addr = self.builder.add(
            self.builder.load(self.regs[ra]),
            ir.Constant(ir.IntType(8), off),
        )

        unmapped_ram_case = self.builder.append_basic_block()

        self.builder.position_after(calc_addr)
        switch = self.builder.switch(
            calc_addr,
            unmapped_ram_case,
        )

        self.builder.position_at_start(unmapped_ram_case)
        elem_ptr = self.builder.gep(
            self.ram,
            [calc_addr],
        )
        if rb != 0:
            self.builder.store(
                self.builder.load(elem_ptr),
                self.regs[rb],
            )
        self.builder.branch(self.find_next_closest_block(pc))

        get_pixel_case = self.builder.append_basic_block()
        self.builder.position_at_start(get_pixel_case)
        if self.headless:
            self.builder.store(
                ir.Constant(ir.IntType(8), 0),
                self.regs[rb],
            )
        else:
            val = self.builder.call(
                self.funcs["get_pixel"],
                [
                    self.builder.load(self.pixel_x),
                    self.builder.load(self.pixel_y),
                ],
            )
            if rb != 0:
                self.builder.store(
                    val,
                    self.regs[rb],
                )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 244), get_pixel_case)

        get_random_num_case = self.builder.append_basic_block()
        self.builder.position_at_start(get_random_num_case)
        val = self.builder.call(
            self.funcs["get_random_num"],
            [],
        )
        if rb != 0:
            self.builder.store(
                val,
                self.regs[rb],
            )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 254), get_random_num_case)

        get_controller_case = self.builder.append_basic_block()
        self.builder.position_at_start(get_controller_case)
        if self.headless:
            self.builder.store(
                ir.Constant(ir.IntType(8), 0),
                self.regs[rb],
            )
        else:
            val = self.builder.call(
                self.funcs["get_controller"],
                [],
            )
            if rb != 0:
                self.builder.store(
                    val,
                    self.regs[rb],
                )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 255), get_controller_case)

    def instr_str(self, pc, ra, off, rb) -> None:
        calc_addr = self.builder.add(
            self.builder.load(self.regs[ra]),
            ir.Constant(ir.IntType(8), off),
        )

        unmapped_ram_case = self.builder.append_basic_block()

        self.builder.position_after(calc_addr)
        switch = self.builder.switch(
            calc_addr,
            unmapped_ram_case,
        )

        self.builder.position_at_start(unmapped_ram_case)
        is_in_invalid_ram = self.builder.icmp_unsigned(
            ">=",
            calc_addr,
            ir.Constant(ir.IntType(8), 240),
        )
        valid_ram_block = self.builder.append_basic_block()
        self.builder.cbranch(
            is_in_invalid_ram,
            self.error_block,
            valid_ram_block,
        )
        self.builder.position_at_start(valid_ram_block)
        elem_ptr = self.builder.gep(
            self.ram,
            [calc_addr],
        )
        self.builder.store(
            self.builder.load(self.regs[rb]),
            elem_ptr,
        )
        self.builder.branch(self.find_next_closest_block(pc))

        store_pixel_x_case = self.builder.append_basic_block()
        self.builder.position_at_start(store_pixel_x_case)
        self.builder.store(
            self.builder.load(self.regs[rb]),
            self.pixel_x,
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 240), store_pixel_x_case)

        store_pixel_y_case = self.builder.append_basic_block()
        self.builder.position_at_start(store_pixel_y_case)
        self.builder.store(
            self.builder.load(self.regs[rb]),
            self.pixel_y,
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 241), store_pixel_y_case)

        draw_pixel_case = self.builder.append_basic_block()
        self.builder.position_at_start(draw_pixel_case)
        if not self.headless:
            self.builder.call(
                self.funcs["draw_pixel"],
                [
                    self.builder.load(self.pixel_x),
                    self.builder.load(self.pixel_y),
                ],
            )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 242), draw_pixel_case)

        clear_pixel_case = self.builder.append_basic_block()
        self.builder.position_at_start(clear_pixel_case)
        if not self.headless:
            self.builder.call(
                self.funcs["clear_pixel"],
                [
                    self.builder.load(self.pixel_x),
                    self.builder.load(self.pixel_y),
                ],
            )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 243), clear_pixel_case)

        update_screen_case = self.builder.append_basic_block()
        self.builder.position_at_start(update_screen_case)
        if not self.headless:
            self.builder.call(
                self.funcs["update_screen"],
                [],
            )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 245), update_screen_case)

        clear_screen_case = self.builder.append_basic_block()
        self.builder.position_at_start(clear_screen_case)
        if not self.headless:
            self.builder.call(
                self.funcs["clear_screen"],
                [],
            )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 246), clear_screen_case)

        push_char_case = self.builder.append_basic_block()
        self.builder.position_at_start(push_char_case)
        self.builder.call(
            self.funcs["push_char"],
            [self.builder.load(self.regs[rb])],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 247), push_char_case)

        flush_char_buffer_case = self.builder.append_basic_block()
        self.builder.position_at_start(flush_char_buffer_case)
        self.builder.call(
            self.funcs["flush_char_buffer"],
            [],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 248), flush_char_buffer_case)

        clear_char_buffer_case = self.builder.append_basic_block()
        self.builder.position_at_start(clear_char_buffer_case)
        self.builder.call(
            self.funcs["clear_char_buffer"],
            [],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 249), clear_char_buffer_case)

        set_num_to_val_case = self.builder.append_basic_block()
        self.builder.position_at_start(set_num_to_val_case)
        self.builder.call(
            self.funcs["set_num"],
            [self.builder.load(self.regs[rb])],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 250), set_num_to_val_case)

        set_num_to_zero_case = self.builder.append_basic_block()
        self.builder.position_at_start(set_num_to_zero_case)
        self.builder.call(
            self.funcs["set_num"],
            [ir.Constant(ir.IntType(8), 0)],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 251), set_num_to_zero_case)

        unset_signedness_case = self.builder.append_basic_block()
        self.builder.position_at_start(unset_signedness_case)
        self.builder.call(
            self.funcs["set_signedness"],
            [ir.Constant(ir.IntType(1), 0)],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 252), unset_signedness_case)

        set_signedness_case = self.builder.append_basic_block()
        self.builder.position_at_start(set_signedness_case)
        self.builder.call(
            self.funcs["set_signedness"],
            [ir.Constant(ir.IntType(1), 1)],
        )
        self.builder.branch(self.find_next_closest_block(pc))
        switch.add_case(ir.Constant(ir.IntType(8), 253), set_signedness_case)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recompiles a BatPU-2 machine code file to LLVM IR.")
    parser.add_argument("in_file", type=str, help="Path to the input .mc file.")
    parser.add_argument("out_file", type=str, help="Path to the output LLVM IR file.")

    parser.add_argument("--headless", action="store_true", help="Run in headless mode without initializing the graphics library.")
    args = parser.parse_args()
    
    recompiler = Recompiler(
        args.in_file,
        args.out_file,
        args.headless,
    )

    recompiler.recompile()
