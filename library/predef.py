from pathlib import Path
import subprocess

# Download Boost.Predef
subprocess.run(["svn", "export", "https://github.com/boostorg/predef/trunk/include/boost", "--force"])
print("did it work?")

# Add extra std and no prefix defines
for path in Path('boost').rglob('*.h'):
    f = open(path, "r").read().split("\n")
    content = ""

    i = 0
    while i < len(f):
        line = f[i]
        if("#" in line):
            while i + 1 < len(f) and f[i].strip().endswith("\\"):
                i += 1
                line += "\n" + f[i]

        content += line + "\n"

        if "#" in line and ("define " in line or "undef " in line) and "BOOST_" in line:
            content += line.replace("BOOST_", "") + "\n"
        i += 1

    f = open(path, "w")
    f.write(content)
    print("Proccessed: ", path)
    f.close()