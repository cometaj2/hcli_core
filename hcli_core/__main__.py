import sys
import re
import shlex
import shutil
import textwrap

from subprocess import call

from hcli_core import package
from hcli_core import config
from hcli_core import hutils
from hcli_core import template

from contextlib import nullcontext

cfg = config.Config()

# helps with printing error messages to STDERR
def eprint(*args, **kwargs):
    msg = ' '.join(str(arg) for arg in args)
    sys.stderr.write(msg)

# prototype generator to identity generators as a type
def generator():
    yield

def main():

    # Only handle and consume -n for huckle commands to help work around terminal aesthetics
    no_newline = False
    if len(sys.argv) > 0 and (sys.argv[0] == "hcli_core" or 
        (len(sys.argv) > 1 and sys.argv[0].endswith("hcli_core"))):
        if '-n' in sys.argv:
            no_newline = True
            sys.argv.remove('-n')

    try:
        # Read from stdin if there's input available
        input_data = None
        if not sys.stdin.isatty():
            input_data = sys.stdin.buffer.read()

        output = None
        with stdin(input_data) if input_data else nullcontext():
            output = cli()

        if output is None:
            return

        if isinstance(output, type(generator())):
            dest = None
            stdout_bytes_written = 0
            stderr_bytes_written = 0
            for dest, chunk in output:  # Now unpacking tuple of (dest, chunk)
                stream = sys.stderr if dest == 'stderr' else sys.stdout
                f = getattr(stream, 'buffer', stream)
                if chunk:
                    f.write(chunk)
                    f.flush()

                    # Track total bytes written to each stream
                    if dest == 'stdout':
                        stdout_bytes_written += len(chunk)
                    else:
                        stderr_bytes_written += len(chunk)

                    if dest == 'stderr':
                        try:
                            error = chunk.decode('utf-8')
                            eprint(error)
                        except UnicodeDecodeError:
                            eprint(chunk)

                        # Add newline for stderr before exit if needed
                        if stderr_bytes_written > 0 and not no_newline:
                            sys.stderr.write('\n')
                        sys.exit(1)

            # Add newlines after all output so that other *nix tools will work correctly
            if not no_newline:
                if dest == 'stdout' and stdout_bytes_written > 0:
                    sys.stdout.write('\n')
                elif dest == 'stderr' and sterr_bytes_written > 0:
                    eprint('\n')
        else:
            error = "hcli_core: unexpected non-generator type."
            eprint(error)
            if not no_newline:
                eprint('\n')
    except Exception as error:
        eprint(error)
        if not no_newline:
            eprint('\n')
        sys.exit(1)

def cli():
    if len(sys.argv) == 1:
        return hcli_core_help()

    if sys.argv[1] == "--version":
        return show_dependencies()

    elif sys.argv[1] == "help":
        help = display_man_page(cfg.hcli_core_manpage_path)

        def generator():
            yield ('stdout', help)

        return generator()

    elif sys.argv[1] == "path":

        def generator():
            yield ('stdout', (cfg.root).encode('utf-8'))

        return generator()

    elif sys.argv[1] == "sample":
        sample = None
        if len(sys.argv) > 2:

            if sys.argv[2] == "hub":
                sample = cfg.sample + "/hub/cli"
            elif sys.argv[2] == "hfm":
                sample = cfg.sample + "/hfm/cli"
            elif sys.argv[2] == "nw":
                sample = cfg.sample + "/nw/cli"
            elif sys.argv[2] == "hptt":
                sample = cfg.sample + "/hptt/cli"
            else:
                return hcli_core_help()

            def generator():
                yield ('stdout', sample.encode('utf-8'))

            return generator()

    elif sys.argv[1] == "cli" and sys.argv[2] == "install":
        if len(sys.argv) == 4:
            t = template.Template(sys.argv[3])
            root = t.findRoot()
            name = config.create_configuration(root["name"], sys.argv[3], root["section"][0]["description"])

            def generator():
                yield ('stdout', name.encode('utf-8'))

            return generator()
        else:
            return hcli_core_help()

    elif sys.argv[1] == "cli" and sys.argv[2] == "config":
        if len(sys.argv) == 4:
            return config.config_list(sys.argv[3])
        elif len(sys.argv) == 5:
            return config.get_parameter(sys.argv[3], sys.argv[4])
        elif len(sys.argv) == 6:
            if sys.argv[4] == "--unset":
                return config.unset_parameter(sys.argv[3], sys.argv[5])
            else:
                return config.update_parameter(sys.argv[3], sys.argv[4], sys.argv[5])
        else:
            return hcli_core_help()

    elif sys.argv[1] == "cli" and sys.argv[2] == "ls":
        return config.list_clis()

    elif sys.argv[1] == "cli" and sys.argv[2] == "rm":
        if len(sys.argv) > 3:
            return config.remove_cli(sys.argv[3])

        else:
            return hcli_core_help()

    elif sys.argv[1] == "cli" and sys.argv[2] == "run":
        if len(sys.argv) > 3:
            return config.run_cli(sys.argv[3])

    else:
        return hcli_core_help()

    return hcli_core_help()

def show_dependencies():
    def parse_dependency(dep_string):
        # Common version specifiers
        specifiers = ['==', '>=', '<=', '~=', '>', '<', '!=']

        # Find the first matching specifier
        for specifier in specifiers:
            if specifier in dep_string:
                name, version = dep_string.split(specifier, 1)
                return name.strip(), specifier, version.strip()

        # If no specifier found, return just the name
        return dep_string.strip(), '', ''

    dependencies = ""
    for dep in package.dependencies:
        name, specifier, version = parse_dependency(dep)
        if version:  # Only add separator if there's a version
            dependencies += f" {name}/{version}"
        else:
            dependencies += f" {name}"

    def generator():
        yield ('stdout', f"hcli_core/{package.__version__}{dependencies}".encode('utf-8'))

    return generator()

def hcli_core_help():
    error = "for help, use:\n\n  hcli_core help"
    raise Exception(error)

# displays a man page (file) located on a given path
def display_man_page(path):
    with open(path, "r") as f:
        text = f.read()
        return troff_to_text(text).encode('utf-8')
    f.close()
    #call(["man", path])

def troff_to_text(content, width=None):
    # If width is not specified, try to get the terminal size
    if width is None:
        try:
            columns, _ = shutil.get_terminal_size()
            width = columns
        except Exception:
            # Fall back to 80 if we can't determine terminal size
            width = 80

    # Helper function to handle troff escape characters
    def process_escapes(text):
        # Generic rule: remove backslash before any character
        text = re.sub(r'\\(.)', r'\1', text)
        return text

    # Extract the man page title from .TH line
    title_match = re.search(r'\.TH\s+(\S+)\s+(\S+)', content)
    if title_match:
        name = title_match.group(1)
        section = title_match.group(2)
        name_section = f"{name}({section})"
        centered_text = "User Commands"

        # Calculate proper alignment positions for header
        left_text = name_section
        center_text = centered_text
        right_text = name_section

        # Create properly aligned header
        left_part = left_text
        center_start = (width - len(center_text)) // 2
        center_part = " " * (center_start - len(left_part)) + center_text
        right_start = width - len(right_text)
        right_part = " " * (right_start - len(left_part) - len(center_part)) + right_text

        header = left_part + center_part + right_part

        # Create right-aligned footer
        footer = " " * (width - len(name_section)) + name_section
    else:
        header = ""
        footer = ""

    # Initialize result with header
    result = [header, ""] if header else []

    # Process the content line by line
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('.B'):
            # For top-level .B directives, collect them as part of the next regular text
            bold_text = line[2:].strip()
            i += 1
            continue

        # Process .SH (section header)
        if line.startswith('.SH'):
            # Add only a single blank line before section header
            if result and result[-1] != "":
                result.append("")
            section_name = process_escapes(line[4:].strip().strip('"'))
            result.append(section_name)
            i += 1

            # Process the content until the next .SH or end
            section_content = []
            paragraph_lines = []
            is_first_ip = True  # Flag to track first .IP in section

            while i < len(lines):
                current = lines[i].strip()

                # Check for next section header
                if current.startswith('.SH'):
                    break

                if current.startswith('.B'):
                    bold_text = current[2:].strip()
                    if bold_text:
                        paragraph_lines.append(bold_text)
                    i += 1
                    continue

                # Process subsection header (.SS)
                if current.startswith('.SS'):
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines)
                        wrapped_lines = textwrap.wrap(para_text, width=width-7)
                        for wrapped_line in wrapped_lines:
                            result.append(f"       {wrapped_line}")
                        result.append("")
                        paragraph_lines = []

                    if result and result[-1] != "":
                        result.append("")
                    subsection_name = process_escapes(current[4:].strip().strip('"'))
                    result.append(f"   {subsection_name}")
                    i += 1
                    is_first_ip = True  # Reset flag for new subsection
                    continue

                # Process indented paragraph (.IP)
                if current.startswith('.IP'):
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines)
                        wrapped_lines = textwrap.wrap(para_text, width=width-7)
                        for wrapped_line in wrapped_lines:
                            result.append(f"       {wrapped_line}")
                        paragraph_lines = []

                    # Add blank line before .IP entry only if it's not the first .IP
                    if not is_first_ip:
                        result.append("")

                    is_first_ip = False  # Update flag after processing first .IP

                    item_match = re.search(r'\.IP\s+"([^"]+)"', current)
                    if item_match:
                        item_name = process_escapes(item_match.group(1))
                    else:
                        item_name = process_escapes(current[3:].strip().strip('"'))

                    result.append(f"       {item_name}")
                    i += 1

                    desc_text = []
                    # Check for .B immediately following .IP
                    if i < len(lines) and lines[i].strip().startswith('.B'):
                        bold_text = process_escapes(lines[i].strip()[2:].strip())
                        if bold_text:
                            desc_text.append(bold_text)
                        i += 1

                    while i < len(lines) and not (lines[i].strip().startswith('.') and 
                                               not lines[i].strip().startswith('.br') and 
                                               not lines[i].strip().startswith('.sp') and
                                               not lines[i].strip().startswith('.B')):
                        if lines[i].strip().startswith('.sp'):
                            if desc_text:
                                wrapped_desc = textwrap.wrap(' '.join(desc_text), width=width-14)
                                for wrapped_line in wrapped_desc:
                                    result.append(f"              {wrapped_line}")
                                result.append("")
                                desc_text = []
                        elif lines[i].strip().startswith('.br'):
                            if desc_text:
                                wrapped_desc = textwrap.wrap(' '.join(desc_text), width=width-14)
                                for wrapped_line in wrapped_desc:
                                    result.append(f"              {wrapped_line}")
                                desc_text = []
                        elif lines[i].strip().startswith('.B'):
                            if desc_text:
                                wrapped_desc = textwrap.wrap(' '.join(desc_text), width=width-14)
                                for wrapped_line in wrapped_desc:
                                    result.append(f"              {wrapped_line}")
                                desc_text = []
                        else:
                            if not lines[i].strip().startswith('.'):
                                desc_text.append(lines[i].strip())
                        i += 1

                    if desc_text:
                        wrapped_desc = textwrap.wrap(' '.join(desc_text), width=width-14)
                        for wrapped_line in wrapped_desc:
                            result.append(f"              {wrapped_line}")

                    continue

                if current.startswith('.sp'):
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines)
                        wrapped_lines = textwrap.wrap(para_text, width=width-7)
                        for wrapped_line in wrapped_lines:
                            result.append(f"       {wrapped_line}")
                        result.append("")
                        paragraph_lines = []
                    i += 1
                    continue

                if current.startswith('.br'):
                    if paragraph_lines:
                        para_text = ' '.join(paragraph_lines)
                        wrapped_lines = textwrap.wrap(para_text, width=width-7)
                        for wrapped_line in wrapped_lines:
                            result.append(f"       {wrapped_line}")
                        paragraph_lines = []
                    i += 1
                    continue

                if not current.startswith('.'):
                    processed_text = process_escapes(current)
                    paragraph_lines.append(processed_text)

                i += 1

            if paragraph_lines:
                para_text = ' '.join(paragraph_lines)
                wrapped_lines = textwrap.wrap(para_text, width=width-7)
                for wrapped_line in wrapped_lines:
                    result.append(f"       {wrapped_line}")

            continue

        i += 1

    # Add footer with empty line before it
    if footer:
        result.append("")
        result.append(footer)

    return '\n'.join(result)
