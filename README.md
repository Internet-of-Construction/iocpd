<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 14:31:46 2022

@author: GarlefHupfer
"""

=======
>>>>>>> 1e1d2c647a6e37995e8eb018c4a16c689c07e4ef
# Internet of Construction Project Dashboard
Internet of Construction Project Dashboard

Disclaimer: This work is part of the research project “Internet of Construction” that is funded by the Federal Ministry of Education and Research of Germany within the indirective on a joint funding initiative in the field of innovation for production, services and labor of tomorrow (funding number: 02P17D081) and supported by the project management agency “Projektträger Karlsruhe (PTKA)”. The authors are responsible for the content.
<<<<<<< HEAD

# Installation
The library was coded in python 3.9. An anaconda environment is recommended for using it. Following packages are necessary:
*anyio=3.6.2
*astroid=2.11.7
*beautifulsoup4=4.11.1
*json5=0.9.5
*matplotlib=3.6.2
*numpy=1.24.1
*pandas=1.5.2
*pm4py=2.4.1
*requests=2.28.1
*spiffworkflow=1.2.1
*websocket-client=1.5.1

# Dashboard Sources
![Dashboard Sources](https://private-user-images.githubusercontent.com/90630691/250031509-9ef90bf3-4c64-4236-ae87-80d48114ac7a.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJrZXkxIiwiZXhwIjoxNjg4MTEyMzU2LCJuYmYiOjE2ODgxMTIwNTYsInBhdGgiOiIvOTA2MzA2OTEvMjUwMDMxNTA5LTllZjkwYmYzLTRjNjQtNDIzNi1hZTg3LTgwZDQ4MTE0YWM3YS5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBSVdOSllBWDRDU1ZFSDUzQSUyRjIwMjMwNjMwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDIzMDYzMFQwODAwNTZaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1kN2VjZmNlMGI1MDBlN2JkZTRkZGQyZjMyYjE2N2JmZTgwNjc0YjM1OTFhZWM0ZTNkM2NiOGVlNWM5MzE1YjhlJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.ceaqhKkk4UB6nsVkX9OqwEcWficJEUWiPKzIUcV-4SA)

# Recommended setup
![Recommended setup](https://private-user-images.githubusercontent.com/90630691/250031523-94971929-80ed-4d57-b690-edfdba39b7eb.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJrZXkxIiwiZXhwIjoxNjg4MTEyMzU2LCJuYmYiOjE2ODgxMTIwNTYsInBhdGgiOiIvOTA2MzA2OTEvMjUwMDMxNTIzLTk0OTcxOTI5LTgwZWQtNGQ1Ny1iNjkwLWVkZmRiYTM5YjdlYi5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBSVdOSllBWDRDU1ZFSDUzQSUyRjIwMjMwNjMwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDIzMDYzMFQwODAwNTZaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT04ZjRmNzE4MjRhMWE1NmZkNzU1ZDQ3NzBkMmY3NjM0ZDM1MDk5NzY5M2I2MjY1N2UzNmQ1OWJhZDg2MTIyYzZkJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.AsXxkyhXmzjpPESd1klibqH1EahANlqgsBiKMLFgCME))

# Main Loop for updates
![Main loop](https://private-user-images.githubusercontent.com/90630691/250031519-fe62c3b1-ecb2-4561-b2a3-3c89ec3875c1.jpg?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJrZXkxIiwiZXhwIjoxNjg4MTEyMzU2LCJuYmYiOjE2ODgxMTIwNTYsInBhdGgiOiIvOTA2MzA2OTEvMjUwMDMxNTE5LWZlNjJjM2IxLWVjYjItNDU2MS1iMmEzLTNjODllYzM4NzVjMS5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBSVdOSllBWDRDU1ZFSDUzQSUyRjIwMjMwNjMwJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDIzMDYzMFQwODAwNTZaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT00ZWU1YjkyODgwZDgyYjI1NTJmMzU1MTkwMGM5Yjc0MjEwMmQwODJlM2ZhNTJmODY0MzcxOTYwMTMxMGY0YTVjJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZhY3Rvcl9pZD0wJmtleV9pZD0wJnJlcG9faWQ9MCJ9.AlPb4EoAvHW-nxXW6Z0UJALUPTp5EQpeeJK0eUyHjI4))
=======
>>>>>>> 1e1d2c647a6e37995e8eb018c4a16c689c07e4ef
