const std = @import("std");
const rl = @import("raylib");

const SCALE = 16;
const TARGET_FPS = -1;

var screen: rl.Image = undefined;
var texture: rl.Texture2D = undefined;

pub export fn init() void {
    rl.initWindow(32 * SCALE, 32 * SCALE, "BatPU2 Recomp");
    if (TARGET_FPS > 0) {
        rl.setTargetFPS(TARGET_FPS);
    }

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
