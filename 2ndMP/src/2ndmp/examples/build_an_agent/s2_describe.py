"""STEP 2 -- Describe the tool to the model. The model never sees the code, only this description.

Name, what it does, and what each argument means. Good descriptions are most of the skill.
"""
import json

TOOLS = [{
    "type": "function",
    "function": {
        "name": "cantilever_beam",
        "description": "Deflection, stress and safety factor of a cantilever beam with a rectangular section and a "
                       "point load at the free end. Use it for any question about how much a cantilever bends or whether it is safe.",
        "parameters": {
            "type": "object",
            "properties": {
                "load_n": {"type": "number", "description": "load at the free end, newtons"},
                "length_mm": {"type": "number", "description": "beam length, millimetres"},
                "width_mm": {"type": "number", "description": "section width b, millimetres"},
                "height_mm": {"type": "number", "description": "section height h in the direction of the load, millimetres"},
                "material": {"type": "string", "description": "steel, aluminum or titanium"},
            },
            "required": ["load_n", "length_mm", "width_mm", "height_mm"],
        },
    },
}]

if __name__ == "__main__":
    print(json.dumps(TOOLS, indent=2))
