import argparse
import json
from jsonschema import validate, Draft202012Validator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("finding_json", help="Path to finding JSON file")
    parser.add_argument("schema_json", help="Path to schema JSON file (findings.schema)")
    args = parser.parse_args()

    with open(args.finding_json, "r", encoding="utf-8") as f:
        finding = json.load(f)
    with open(args.schema_json, "r", encoding="utf-8") as f:
        schema = json.load(f)

    Draft202012Validator.check_schema(schema)
    validate(instance=finding, schema=schema)
    print("OK: finding matches schema")


if __name__ == "__main__":
    main()


