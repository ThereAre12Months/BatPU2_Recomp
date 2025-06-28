const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});

    const optimize = b.standardOptimizeOption(.{});

    const lib_mod = b.createModule(.{
        .root_source_file = b.path("src/root.zig"),

        .target = target,
        .optimize = optimize,
    });

    const raylib_dep = b.dependency("raylib_zig", .{
        .target = target,
        .optimize = optimize,
        .shared = false,
        //.linux_display_backend = .X11,
    });

    const raylib = raylib_dep.module("raylib");
    const raylib_artifact = raylib_dep.artifact("raylib");

    lib_mod.linkLibrary(raylib_artifact);
    lib_mod.addImport("raylib", raylib);

    const lib = b.addStaticLibrary(.{
        .name = "helper_funcs",
        .root_module = lib_mod,
        .optimize = optimize,
    });

    b.installArtifact(raylib_artifact);
    b.installArtifact(lib);
}
