/* link.ld - 128 KiB RAM at address 0, stack at the top. */
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0x00000000, LENGTH = 128K }
SECTIONS {
	.text : { KEEP(*(.text.start)) *(.text*) } > RAM
	.rodata : { *(.rodata*) *(.srodata*) } > RAM
	.data : { *(.data*) *(.sdata*) } > RAM
	.bss : { _bss_start = .; *(.bss*) *(.sbss*) *(COMMON) . = ALIGN(4); _bss_end = .; } > RAM
	/DISCARD/ : { *(.note*) *(.comment) *(.eh_frame*) }
	_stack_top = ORIGIN(RAM) + LENGTH(RAM);
}
