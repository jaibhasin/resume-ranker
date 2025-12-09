import argparse
import os

def get_args():
    parser = argparse.ArgumentParser(description="Resume Ranking")

    parser.add_argument("--files", nargs="*", help="Explicit resume file paths")
    parser.add_argument("--folder", help="Folder containing resume files")

    return parser.parse_args()


def collect_resume_files(args):
    valid_ext = (".pdf", ".docx")

    if args.files:
        files = []
        for f in args.files:
            if not os.path.exists(f):
                print(f"Warning: File not found: {f}")
                continue
            if not f.lower().endswith(valid_ext):
                print(f"Warning: Skipping unsupported file type: {f}")
                continue
            files.append(f)
        return files[:10]
    
    if args.folder:
        if not os.path.isdir(args.folder):
            print("Invalid folder path.")
            return []

        resume_files = []
        for fname in os.listdir(args.folder):
            if fname.lower().endswith(valid_ext):
                full_path = os.path.join(args.folder, fname)
                if os.path.isfile(full_path):
                    resume_files.append(full_path)
                    if len(resume_files) == 10:
                        break

        return resume_files

    print("Error: Provide either --files or --folder")
    return []

if __name__ == "__main__":
    args = get_args()
    resumes = collect_resume_files(args)

    print("Selected files:")
    for r in resumes:
        print(" -", r)
