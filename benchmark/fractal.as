; draws the sierpinski triangle 256 times
; updating the screen every pixel

jmp .main

.triangle
ldi r14 32
.t_loop_x
ldi r15 32
.t_loop_y

ldi r1 1
sub r14 r1 r2
sub r15 r1 r3
and r2 r3 r0
brh ne .t_skip

ldi r1 240
str r1 r2
ldi r1 241
str r1 r3
ldi r1 242
str r1 r0

ldi r1 245
str r1 r0

.t_skip

adi r15 255
brh ne .t_loop_y

adi r14 255
brh ne .t_loop_x

ret

.main
ldi r9 0
.main_loop
ldi r1 246
str r1 r0
ldi r1 245
str r1 r0
cal .triangle
adi r9 255
brh ne .main_loop

hlt