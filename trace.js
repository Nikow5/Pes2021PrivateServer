/*
    PES2021 Server Connection Tracer
    Target Version: 1.07.02
*/

const base = Module.findBaseAddress("PES2021.exe");

if (base) {
    console.log("[*] PES2021.exe base address: " + base);

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
                // +0x00: VTable
                // +0x08: Server ID (4 bytes, Big Endian)
                // +0x0C: Server Type (4 bytes)
                // +0x10: IP Address (4 bytes)
                // +0x14: Port (2 bytes, Little Endian)
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

            // Check flags
            // GlobalState + 0x14
            // ConnectGateTask + 0x8A
            // Assuming 'this.obj' points to the relevant structure (ConnectGateTask or similar)

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
    console.error("Error: PES2021.exe module not found. Make sure the game is running.");
}
