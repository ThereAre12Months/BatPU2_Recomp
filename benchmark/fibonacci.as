; calculates the least significant 8 bits of the 2^32th fibonacci number

ldi r1 0
ldi r2 1

ldi r4 0
.loop_r4

ldi r5 0
.loop_r5

ldi r6 0
.loop_r6

ldi r7 0
.loop_r7

add r1 r2 r3
xor r2 r0 r1
xor r3 r0 r2

adi r7 255
brh ne .loop_r7

adi r6 255
brh ne .loop_r6

adi r5 255
brh ne .loop_r5

adi r4 255
brh ne .loop_r4

ldi r4 250
str r4 r3

hlt