const std = @import("std");
const rl = @import("raylib");

const SCALE = 16;
const TARGET_FPS = -1;

var screen: rl.Image = undefined;
var texture: rl.Texture2D = undefined;

var char_buffer: [32]u8 = .{0} ** 32;
var char_buffer_index: usize = 0;
var char_mapping: [256]u8 = undefined;

var num: u8 = 0;
var signedness: bool = false;

var writer: std.fs.File.Writer = undefined;

pub export fn init() void {
    rl.initWindow(32 * SCALE, 32 * SCALE, "BatPU2 Recomp");
    if (TARGET_FPS > 0) {
        rl.setTargetFPS(TARGET_FPS);
    }

    writer = std.io.getStdOut().writer();

    // init screen buffer
    screen = rl.genImageColor(32, 32, rl.Color.black);
    texture = rl.loadTextureFromImage(screen) catch return;

    rl.beginDrawing();
    clear_screen();

    update_screen();
}

pub export fn deinit() void {
    screen.unload();
    texture.unload();

    rl.endDrawing();
    rl.closeWindow();

    std.process.exit(0);
}

pub export fn draw_pixel(x: u8, y: u8) void {
    screen.drawPixel(x, 31 - y, rl.Color.white);
}

pub export fn clear_pixel(x: u8, y: u8) void {
    screen.drawPixel(x, 31 - y, rl.Color.black);
}

pub export fn get_pixel(x: u8, y: u8) u8 {
    return screen.getColor(x, 31 - y).r & 1;
}

pub export fn clear_screen() void {
    screen.clearBackground(rl.Color.black);
}

pub export fn update_screen() void {
    // this is probably the most inneficient way to do this
    rl.updateTexture(texture, screen.data);
    rl.drawTextureEx(texture, .{ .x = 0, .y = 0 }, 0.0, SCALE, rl.Color.white);
    rl.endDrawing();
    rl.beginDrawing();

    if (rl.windowShouldClose()) {
        deinit();
        std.process.exit(0);
    }
}

fn map_char(c: u8) u8 {
    if (c == 0) {
        return ' ';
    }
    if (c < 27) {
        return @intCast('A' + c - 1);
    }
    if (c == 27) {
        return '.';
    }
    if (c == 28) {
        return '!';
    }
    if (c == 29) {
        return '?';
    }

    // '-' is used for undefined characters
    return '-';
}

pub export fn push_char(c: u8) void {
    if (char_buffer_index < char_buffer.len) {
        char_buffer[char_buffer_index] = map_char(c);
        char_buffer_index += 1;
    }
}

pub export fn clear_char_buffer() void {
    char_buffer = .{0} ** 32;
    char_buffer_index = 0;
}

pub export fn flush_char_buffer() void {
    if (char_buffer_index > 0) {
        writer.print("{s}\n", .{char_buffer[0..char_buffer.len]}) catch return;
        clear_char_buffer();
    }
}

pub export fn set_num(n: u8) void {
    num = n;
}

pub export fn set_signedness(signed: bool) void {
    signedness = signed;
}

pub export fn write_num() void {
    if (signedness) {
        writer.print("{d}\n", .{@as(i16, num & 0b01111111) * -@as(i16, num >> 7)}) catch return;
    } else {
        writer.print("{u}\n", .{@as(u8, num)}) catch return;
    }
}

pub export fn get_controller() u8 {
    // START  : enter
    // SELECT : space
    // A      : w
    // B      : x
    // UP     : up arrow
    // RIGHT  : right arrow
    // DOWN   : down arrow
    // LEFT   : left arrow

    var controller: u8 = 0;

    rl.pollInputEvents();

    // start
    if (rl.isKeyDown(rl.KeyboardKey.enter)) {
        controller |= 0b10000000;
    }

    // select
    if (rl.isKeyDown(rl.KeyboardKey.space)) {
        controller |= 0b01000000;
    }

    // A
    if (rl.isKeyDown(rl.KeyboardKey.a) or
        rl.isKeyDown(rl.KeyboardKey.w))
    {
        controller |= 0b00100000;
    }

    // B
    if (rl.isKeyDown(rl.KeyboardKey.x)) {
        controller |= 0b00010000;
    }

    // up
    if (rl.isKeyDown(rl.KeyboardKey.up)) {
        controller |= 0b00001000;
    }

    // right
    if (rl.isKeyDown(rl.KeyboardKey.right)) {
        controller |= 0b00000100;
    }

    // down
    if (rl.isKeyDown(rl.KeyboardKey.down)) {
        controller |= 0b00000010;
    }

    // left
    if (rl.isKeyDown(rl.KeyboardKey.left)) {
        controller |= 0b00000001;
    }

    return controller;
}

pub export fn get_random_num() u8 {
    return @intCast(rl.getRandomValue(0, 256));
}
