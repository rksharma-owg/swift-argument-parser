import json, re, subprocess, sys, tempfile
from pathlib import Path
root = Path(sys.argv[1]).resolve()
paths = ["README.md", "Sources/ArgumentParser/Documentation.docc/ArgumentParser.md", "Sources/ArgumentParser/Documentation.docc/Extensions/ParsableCommand.md"]
with tempfile.TemporaryDirectory(prefix="repeat-doc-examples-") as temporary:
    package = Path(temporary)
    targets = []
    for index, path in enumerate(paths):
        name = f"Example{index}"
        code = re.search(r"```swift\n(.*?)\n```", (root / path).read_text(), re.S).group(1)
        if "import ArgumentParser" not in code:
            code = "import ArgumentParser\n" + code
        source = package / "Sources" / name
        source.mkdir(parents=True)
        (source / "Repeat.swift").write_text(code)
        targets.append(f'.executableTarget(name: "{name}", dependencies: [.product(name: "ArgumentParser", package: "{root.name.lower()}")])')
    manifest = '// swift-tools-version: 6.0\nimport PackageDescription\nlet package = Package(name: "RepeatDocumentation", dependencies: [.package(path: ' + json.dumps(str(root)) + ')], targets: [' + ','.join(targets) + '])\n'
    (package / "Package.swift").write_text(manifest)
    subprocess.run(["swift", "build", "--package-path", str(package)], check=True)
    for index in range(len(paths)):
        executable = package / ".build" / "debug" / f"Example{index}"
        for arguments, status, output in [(["hello"], 0, "hello\nhello\n"), (["hello", "--count", "0"], 0, ""), (["hello", "--count=-1"], 64, None)]:
            result = subprocess.run([str(executable)] + arguments, capture_output=True, text=True)
            assert result.returncode == status, (paths[index], arguments, result.returncode, result.stderr)
            if output is not None:
                assert result.stdout == output, (paths[index], result.stdout)
            else:
                assert "Count must be zero or greater." in result.stderr, result.stderr
            print(paths[index], arguments, "PASS")
