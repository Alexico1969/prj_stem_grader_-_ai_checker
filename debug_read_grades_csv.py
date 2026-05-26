import csv

with open('grades.csv', 'r', encoding='utf-8') as f:
    r = csv.reader(f)
    header = next(r)
    next(r)
    assignments = header[5:]
    print('Assignments count:', len(assignments))
    for a in assignments[:10]:
        print('-', a)
    prefixes = []
    for a in assignments:
        tok = a.strip().split()[0] if a.strip() else ''
        if tok and tok not in prefixes:
            prefixes.append(tok)
    print('Prefixes count:', len(prefixes))
    print(prefixes[:20])
