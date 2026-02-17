# PES2021 Server Connection Tracer

This project provides a Frida script to trace and debug the PES2021 (v1.07.02) server connection phase. It uses critical memory addresses and offsets provided to hook into the game process and monitor the connection flow.

## Usage

1.  Ensure you have Frida installed (`pip install frida-tools`).
2.  Run the game `PES2021.exe`.
3.  Inject the script using Frida:
    ```bash
    frida -n PES2021.exe -l trace.js
    ```

## Features

-   **Validator Hook**: Checks if the Server Entry VTable is correct (`0x14285B5B0`) to prevent `C_IDGG_0002` errors.
-   **State Transition Monitoring**: Traces the transition to the main menu (State 10) and checks success flags.
-   **Additional Hooks**: Monitors State 5 (Steam Ticket) and State 6 (Server List) handlers.

## Critical Offsets (v1.07.02)

| Name | Address (RVA) | Description |
| :--- | :--- | :--- |
| **XOR Key (NclMio)** | `0x143523BCC` | Cyclic key used for decryption. |
| **Server Entry VTable** | `0x14285B5B0` | Must be present at `+0x00` of each server entry. |
| **State 5 Handler** | `0x140FE0C50` | Handles Steam Ticket sending. |
| **State 6 Handler** | `0x140FE1FE0` | Handles Server List reception. |
| **Packet Validator** | `0x1411AEEC0` | Validates server entries. |
| **NclMio Deserialize** | `0x141859B90` | Main parser. |
| **Task 627 Manager** | `0x140FE31B0` | Connection manager. |

## License

MIT
