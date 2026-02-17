/*
    PES2021 Server Connection Tracer
    Target Version: 1.07.02
*/

function getBaseAddress() {
    // Attempt 1: Standard Module.findBaseAddress
    // This is most precise if the module name matches exactly.
    const moduleName = "PES2021.exe";
    let base = Module.findBaseAddress(moduleName);

    if (base) {
        console.log("[*] Found base via Module.findBaseAddress('" + moduleName + "'): " + base);
        return base;
    }

    // Attempt 2: Process.enumerateModules() - First module usually is the main executable
    console.log("[*] Module.findBaseAddress returned null. Trying enumeration...");
    const modules = Process.enumerateModules();
    if (modules.length > 0) {
        // Look for something containing "PES2021"
        for (let i = 0; i < modules.length; i++) {
            if (modules[i].name.indexOf("PES2021") !== -1) {
                console.log("[*] Found module via enumeration: " + modules[i].name + " @ " + modules[i].base);
                return modules[i].base;
            }
        }
        // Fallback: Just return the first module base (often the main exe)
        console.log("[*] Specific module not found. Using first module: " + modules[0].name + " @ " + modules[0].base);
        return modules[0].base;
    }

    return null;
}

if (typeof Interceptor === 'undefined') {
    console.error("Error: This script must be run within Frida (e.g., 'frida -n PES2021.exe -l trace.js').");
} else {
    try {
        const base = getBaseAddress();

        if (base) {
            console.log("[*] Base Address for Hooks: " + base);

            // --- Critical Offsets (Relative to Base) ---
            // Calculated by subtracting default base 0x140000000 from provided addresses
            const OFFSET_VALIDATOR = 0x11AEEC0;     // 0x1411AEEC0
            const OFFSET_STATE_10 = 0xFF3EC0;       // 0x140FF3EC0
            const OFFSET_STATE_5 = 0xFE0C50;        // 0x140FE0C50
            const OFFSET_STATE_6 = 0xFE1FE0;        // 0x140FE1FE0
            const OFFSET_VTABLE = 0x285B5B0;        // 0x14285B5B0

            // --- Hooks ---

            // 1. Packet Validator (Source of C_IDGG_0002 error)
            // 0x1411AEEC0
            const addrValidator = base.add(OFFSET_VALIDATOR);
            Interceptor.attach(addrValidator, {
                onEnter: function(args) {
                    // args[0] points to the start of the 32-byte server entry
                    try {
                        // The VTable pointer is at +0x00
                        var vtable = args[0].readU64();

                        // Calculate expected VTable address based on current base
                        var expectedVTable = base.add(OFFSET_VTABLE);

                        console.log("[Validator] Checking VTable at " + args[0] + ": " + vtable.toString(16));

                        if (vtable.equals(expectedVTable)) {
                            console.log("[Validator] VTable valid.");
                        } else {
                            console.warn("!!! INVALID VTABLE - CRASH EMINENT !!!");
                            console.warn("Expected: " + expectedVTable.toString(16));
                            console.warn("Got:      " + vtable.toString(16));
                        }

                        // Dump the server entry for inspection
                        console.log("[Validator] ServerEntry Dump:");
                        console.log(hexdump(args[0], { length: 32, header: true }));

                    } catch (e) {
                        console.error("[Validator] Error reading memory: " + e);
                    }
                }
            });

            // 2. State 10 Transition (Success Flags)
            // 0x140FF3EC0
            const addrState10 = base.add(OFFSET_STATE_10);
            Interceptor.attach(addrState10, {
                onEnter: function(args) {
                     console.log("[State 10] Transition initiated (Enter).");
                     // Save 'this' (RCX/ECX) to access members later
                     this.obj = args[0];
                },
                onLeave: function(retval) {
                    console.log("[State 10] Transition completed (Leave).");

                    if (this.obj) {
                        try {
                            var flag14 = this.obj.add(0x14).readU8();
                            var flag8A = this.obj.add(0x8A).readU8(); // 0x8A = 138 decimal

                            console.log("[State 10] Flags Check:");
                            console.log("  Flag +0x14: " + flag14);
                            console.log("  Flag +0x8A: " + flag8A);

                            if (flag14 === 1 && flag8A === 1) {
                                 console.log("[State 10] SUCCESS: Flags indicate successful connection.");
                            } else {
                                 console.warn("[State 10] WARNING: Flags do not indicate full success yet.");
                            }
                        } catch (e) {
                            console.error("[State 10] Error reading flags: " + e);
                        }
                    }
                }
            });

            // 3. State 5 Handler (Steam Ticket / CmdLobbyInit)
            // 0x140FE0C50
            const addrState5 = base.add(OFFSET_STATE_5);
            Interceptor.attach(addrState5, {
                onEnter: function(args) {
                    console.log("[State 5] Sending Steam Ticket (CmdLobbyInit).");
                }
            });

            // 4. State 6 Handler (Server List / CmdGetSvrList)
            // 0x140FE1FE0
            const addrState6 = base.add(OFFSET_STATE_6);
            Interceptor.attach(addrState6, {
                onEnter: function(args) {
                    console.log("[State 6] Receiving Server List (CmdGetSvrList).");
                }
            });

            console.log("[*] Hooks installed successfully.");

        } else {
            console.error("Error: Could not find base address for PES2021.exe (or similar module).");
        }
    } catch (e) {
        console.error("Critical Error during initialization: " + e);
    }
}
