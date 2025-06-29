from llvmlite import ir, binding
import os

def load_mc_file(path:str) -> bytes: 
    """
    Load a machine code file from the given path and returns its content as bytes.
    """

    with open(path, "r") as file:
        lines = file.read().splitlines()

    # Convert weird binary strings to bytes
    b = []
    for line in lines:
        b.extend(
            [int(line[:8], base=2), int(line[8:16], base=2)]
        )

    return bytes(b)

def init():
    """
    Initializes the LLVM bindings.
    """

    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_native_asmprinter()

def make_module(name:str):
    """
    Creates a new LLVM module with the given name.
    """

    mod = ir.Module(name=name)
    mod.triple = binding.get_default_triple()
    return mod

def declare_external_functions(mod:ir.Module) -> dict:
    """
    Creates a mapping between function names and their LLVM declarations.
    """

    mapping = {
        "init": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "init",
        ),
        "deinit": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "deinit",
        ),
        "draw_pixel": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8), ir.IntType(8)]),
            name   = "draw_pixel",
        ),
        "clear_pixel": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8), ir.IntType(8)]),
            name   = "clear_pixel",
        ),
        "get_pixel": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.IntType(8), [ir.IntType(8), ir.IntType(8)]),
            name   = "get_pixel",
        ),
        "update_screen": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "update_screen",
        ),
        "clear_screen": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "clear_screen",
        ),
        "push_char": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), [ir.IntType(8)]),
            name   = "push_char",
        ),
        "clear_char_buffer": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "clear_char_buffer",
        ),
        "flush_char_buffer": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.VoidType(), []),
            name   = "flush_char_buffer",
        ),
        "get_controller": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.IntType(8), []),
            name   = "get_controller",
        ),
        "get_random_num": ir.Function(
            module = mod,
            ftype  = ir.FunctionType(ir.IntType(8), []),
            name   = "get_random_num",
        ),
    }
    return mapping

def generate_ir(mod:ir.Module, funcs:dict, mc:bytes) -> str:
    """
    Generates LLVM IR from the given machine code.
    """

    main_func = ir.Function(
        module = mod,
        ftype  = ir.FunctionType(ir.IntType(32), []),
        name   = "main",
    )

    entry = main_func.append_basic_block(name="entry")
    builder = ir.IRBuilder(entry)

    # ram
    ram = builder.alloca(ir.IntType(8), size=256, name="ram")

    # custom stack to better emulate the CAL instruction
    stack = builder.alloca(ir.IntType(16), size=16, name="stack")
    sp    = builder.alloca(ir.IntType(8), name="sp")
    builder.store(ir.Constant(ir.IntType(8), 0), sp)

    # allocate registers on the stack
    regs = [
        builder.alloca(ir.IntType(8), name=f"reg_{reg}") for reg in range(16)
    ]

    # initialize registers to 0
    for reg in regs:
        builder.store(ir.Constant(ir.IntType(8), 0), reg)

    # allocate flags on the stack
    flag_Z = builder.alloca(ir.IntType(1), name="flag_Z")
    flag_C = builder.alloca(ir.IntType(1), name="flag_C")

    builder.store(ir.Constant(ir.IntType(1), 0), flag_Z)
    builder.store(ir.Constant(ir.IntType(1), 0), flag_C)

    # intialize X, Y regs
    pixel_x = builder.alloca(ir.IntType(8), name="pixel_x")
    pixel_y = builder.alloca(ir.IntType(8), name="pixel_y")
    builder.store(ir.Constant(ir.IntType(8), 0), pixel_x)
    builder.store(ir.Constant(ir.IntType(8), 0), pixel_y)

    # create all blocks
    blocks = []
    for i in range(0, len(mc) // 2 + 1):
        blocks.append(
            builder.append_basic_block(name=f"block_{i:04x}")
        )

    builder.call(funcs["init"], [])

    exit_block = builder.append_basic_block(name="exit")
    builder.position_at_start(exit_block)
    builder.call(funcs["deinit"], [])
    builder.ret(ir.Constant(ir.IntType(32), 0))


    builder.position_at_end(entry)
    builder.branch(blocks[0])

    for i in range(0, len(mc), 2):
        builder.position_at_start(blocks[i // 2])

        full = mc[i] << 8 | mc[i + 1]

        opcode = (full & 0xF000) >> 12
        reg_a  = (full & 0x0F00) >> 8 
        reg_b  = (full & 0x00F0) >> 4
        reg_c  = (full & 0x000F)

        offset = (reg_c & 0x7) + bool(reg_c & 0x8) * -8
        if offset < 0:
            offset = 256 + offset

        imm  = full & 0x00FF
        addr = full & 0x03FF

        cond = (full & 0x0C00) >> 10

        match opcode:
            # NOP
            case 0x0:
                pass
            
            # HLT
            # gets emulated by exiting the program
            case 0x1:
                builder.branch(exit_block)

            # ADD
            case 0x2:
                r_a_val = builder.load(regs[reg_a])
                sum_ = builder.add(
                    r_a_val,
                    builder.load(regs[reg_b])
                )
                
                if reg_c != 0:
                    builder.store(
                        sum_,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        sum_,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )
                builder.store(
                    builder.icmp_unsigned(
                        "<",
                        sum_,
                        r_a_val,
                    ),
                    flag_C
                )

            # SUB
            case 0x3:
                r_a_val = builder.load(regs[reg_a])
                res = builder.sub(
                    r_a_val,
                    builder.load(regs[reg_b])
                )

                if reg_c != 0:
                    builder.store(
                        res,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )
                builder.store(
                    builder.icmp_unsigned(
                        ">",
                        res,
                        r_a_val,
                    ),
                    flag_C
                )

            # NOR
            case 0x4:
                res = builder.not_(
                        builder.or_(
                            builder.load(regs[reg_a]),
                            builder.load(regs[reg_b])
                        )
                    )
                
                if reg_c != 0:
                    builder.store(
                        res,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )

            # AND
            case 0x5:
                res = builder.and_(
                    builder.load(regs[reg_a]),
                    builder.load(regs[reg_b]),
                )
                if reg_c != 0:
                    builder.store(
                        res,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )

            # XOR
            case 0x6:
                res = builder.xor(
                        builder.load(regs[reg_a]),
                        builder.load(regs[reg_b])
                    )
                
                if reg_c != 0:
                    builder.store(
                        res,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )

            # RSH
            case 0x7:
                res = builder.lshr(
                    builder.load(regs[reg_a]),
                    ir.Constant(ir.IntType(8), 1),
                )

                if reg_c != 0:
                    builder.store(
                        res,
                        regs[reg_c]
                    )

                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )

            # LDI
            case 0x8:
                if reg_a == 0:
                    continue

                builder.store(
                    ir.Constant(ir.IntType(8), imm),
                    regs[reg_a]
                )

            # ADI
            case 0x9:
                r_a_val = builder.load(regs[reg_a])

                res = builder.add(
                    r_a_val,
                    ir.Constant(ir.IntType(8), imm)
                )
                if reg_a != 0:
                    builder.store(
                        res,
                        regs[reg_a]
                    )
                builder.store(
                    builder.icmp_unsigned(
                        "==",
                        res,
                        ir.Constant(ir.IntType(8), 0)
                    ),
                    flag_Z
                )
                builder.store(
                    builder.icmp_unsigned(
                        "<",
                        res,
                        r_a_val,
                    ),
                    flag_C
                )
            
            # JMP
            case 0xA:
                builder.branch(
                    blocks[addr]
                )

            # BRH
            case 0xB:
                val = None
                if cond == 0:
                    val = builder.icmp_unsigned(
                        "==",
                        builder.load(flag_Z),
                        ir.Constant(ir.IntType(1), 1)
                    )
                elif cond == 1:
                    val = builder.icmp_unsigned(
                        "!=",
                        builder.load(flag_Z),
                        ir.Constant(ir.IntType(1), 1)
                    )
                elif cond == 2:
                    val = builder.icmp_unsigned(
                        "==",
                        builder.load(flag_C),
                        ir.Constant(ir.IntType(1), 1)
                    )
                elif cond == 3:
                    val = builder.icmp_unsigned(
                        "!=",
                        builder.load(flag_C),
                        ir.Constant(ir.IntType(1), 1)
                    )

                builder.cbranch(
                    val,
                    blocks[addr],
                    blocks[i // 2 + 1],
                )

            # CAL
            case 0xC:
                sp0 = builder.load(sp)
                elem_ptr = builder.gep(
                    stack,
                    [sp0],
                    name="sp0"
                )
                builder.store(
                    ir.Constant(ir.IntType(16), i // 2 + 1),
                    elem_ptr,
                )
                builder.store(
                    builder.add(sp0, ir.Constant(ir.IntType(8), 1)),
                    sp
                )

                builder.branch(
                    blocks[addr]
                )

            # RET
            case 0xD:
                new_sp = builder.sub(
                    builder.load(sp),
                    ir.Constant(ir.IntType(8), 1)
                )
                builder.store(
                    new_sp,
                    sp
                )
                elem_ptr = builder.gep(
                    stack,
                    [new_sp],
                )
                ret_addr = builder.load(elem_ptr)

                switch = builder.switch(
                    ret_addr,
                    blocks[i // 2 + 1],
                )

                for j in range(0, len(mc) // 2):
                    switch.add_case(ir.Constant(ir.IntType(16), j), blocks[j])

            # LOD
            case 0xE:
                calc_addr = builder.add(
                    builder.load(regs[reg_a]),
                    ir.Constant(ir.IntType(8), offset)
                )
                is_in_mapped_ram = builder.icmp_unsigned(
                    "<",
                    calc_addr,
                    ir.Constant(ir.IntType(8), 240)
                )

                true_blk = builder.append_basic_block()
                false_blk = builder.append_basic_block()

                builder.position_at_start(true_blk)
                elem_ptr = builder.gep(
                    ram,
                    [calc_addr],
                )
                builder.store(
                    builder.load(elem_ptr),
                    regs[reg_b],
                )

                builder.branch(blocks[i // 2 + 1])

                builder.position_at_start(false_blk)
                switch = builder.switch(
                    calc_addr,
                    blocks[i // 2 + 1],
                )

                case_244 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 244),
                    case_244,
                )
                case_254 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 254),
                    case_254,
                )
                case_255 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 255),
                    case_255,
                )

                builder.position_at_start(case_244)
                val = builder.call(
                    funcs["get_pixel"],
                    [
                        builder.load(pixel_x),
                        builder.load(pixel_y),
                    ]
                )
                builder.store(
                    val,
                    regs[reg_b],
                )
                builder.branch(blocks[i // 2 + 1])

                builder.position_at_start(case_254)
                val = builder.call(
                    funcs["get_random_num"],
                    []
                )
                builder.store(
                    val,
                    regs[reg_b],
                )
                builder.branch(blocks[i // 2 + 1])

                builder.position_at_start(case_255)
                val = builder.call(
                    funcs["get_controller"],
                    []
                )
                builder.store(
                    val,
                    regs[reg_b],
                )
                builder.branch(blocks[i // 2 + 1])

                builder.position_at_end(blocks[i // 2])
                builder.cbranch(
                    is_in_mapped_ram,
                    true_blk,
                    false_blk,
                )

            # STR
            case 0xF:
                calc_addr = builder.add(
                    builder.load(regs[reg_a]),
                    ir.Constant(ir.IntType(8), offset)
                )
                is_in_mapped_ram = builder.icmp_unsigned(
                    "<",
                    calc_addr,
                    ir.Constant(ir.IntType(8), 240)
                )
                true_blk = builder.append_basic_block()
                false_blk = builder.append_basic_block()

                builder.position_at_start(true_blk)
                elem_ptr = builder.gep(
                    ram,
                    [calc_addr],
                )
                builder.store(
                    builder.load(regs[reg_b]),
                    elem_ptr,
                )
                builder.branch(blocks[i // 2 + 1])

                builder.position_at_start(false_blk)
                switch = builder.switch(
                    calc_addr,
                    blocks[i // 2 + 1],
                )

                case_240 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 240),
                    case_240,
                )
                case_241 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 241),
                    case_241,
                )
                case_242 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 242),
                    case_242,
                )
                case_243 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 243),
                    case_243,
                )
                case_245 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 245),
                    case_245,
                )
                case_246 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 246),
                    case_246,
                )
                case_247 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 247),
                    case_247,
                )
                case_248 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 248),
                    case_248,
                )
                case_249 = builder.append_basic_block()
                switch.add_case(
                    ir.Constant(ir.IntType(8), 249),
                    case_249,
                )

                builder.position_at_start(case_240)
                builder.store(
                    builder.load(regs[reg_b]),
                    pixel_x,
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_241)
                builder.store(
                    builder.load(regs[reg_b]),
                    pixel_y,
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_242)
                builder.call(
                    funcs["draw_pixel"],
                    [
                        builder.load(pixel_x),
                        builder.load(pixel_y),
                    ]
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_243)
                builder.call(
                    funcs["clear_pixel"],
                    [
                        builder.load(pixel_x),
                        builder.load(pixel_y),
                    ]
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_245)
                builder.call(
                    funcs["update_screen"],
                    []
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_246)
                builder.call(
                    funcs["clear_screen"],
                    []
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_247)
                builder.call(
                    funcs["push_char"],
                    [builder.load(regs[reg_b])]
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_248)
                builder.call(
                    funcs["flush_char_buffer"],
                    []
                )
                builder.branch(blocks[i // 2 + 1])
                builder.position_at_start(case_249)
                builder.call(
                    funcs["clear_char_buffer"],
                    []
                )
                builder.branch(blocks[i // 2 + 1])

                builder.position_at_end(blocks[i // 2])
                builder.cbranch(
                    is_in_mapped_ram,
                    true_blk,
                    false_blk,
                )

    for idx in range(len(blocks)):
        if idx >= len(blocks) - 1:
            builder.position_at_end(blocks[idx])
            builder.branch(exit_block)
        if not blocks[idx].is_terminated:
            builder.position_at_end(blocks[idx])
            builder.branch(blocks[idx + 1])

    return str(mod)

def recomp(in_file:str, out_file:str):
    """
    Compiles 'in_file' to LLVM IR and writes it to 'out_file'.
    """
    
    init()
    mod = make_module(os.path.basename(in_file))
    funcs = declare_external_functions(mod)

    mc = load_mc_file(in_file)

    llvm = generate_ir(mod, funcs, mc)
    
    with open(out_file, "w") as file:
        
        file.write(llvm)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Recompiles a BatPU-2 machine code file to LLVM IR.")
    parser.add_argument("in_file", type=str, help="Path to the input .mc file.")
    parser.add_argument("out_file", type=str, help="Path to the output LLVM IR file.")

    args = parser.parse_args()

    recomp(args.in_file, args.out_file)