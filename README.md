# Getting started
We are using UV as a package manager. To install it visit https://docs.astral.sh/uv/getting-started/installation/

# How it works
Redirect mavlink with utilities\mav-redirect.sh and then use what you need to use.

We are redirecting mavlink to all needed listeners:

We are listening on:
- "--master=udpin:10.1.1.50:14550"

and redirecting to:
- mav-ctrl.py script that controlls retr carrier: --out=udp:localhost:14990
- QGrooundControll: --out=udp:localhost:14660
- SOVA automatic antenna: --out=udp:localhost:14770
