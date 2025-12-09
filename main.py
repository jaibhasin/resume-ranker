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
        files = [f for f in args.files if f.lower().endswith(valid_ext)]
        return files[:10]  
    if args.folder:
        if not os.path.isdir(args.folder):
            print("Invalid folder path.")
            return []

        all_files = sorted(os.listdir(args.folder))
        resume_files = []

        for fname in all_files:
            if fname.lower().endswith(valid_ext):
                resume_files.append(os.path.join(args.folder, fname))
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
