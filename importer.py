#Final Project - Fenn Edmonds
#used this geeks 4 geeks a lot as a reference: https://www.geeksforgeeks.org/pandas/python-read-csv-using-pandas-read_csv/
from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from classes import Spell, SpellRequirements, SpellClassRequirement

#handle weird csv bools
trueOptions = {"true", "1"}
False_Options = {"false", "0", "", "nan"}

#ye old class lookup tables so i know what level certain spells become avaliable at
fullCaster = {0: 1, 1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 11, 7: 13, 8: 15, 9: 17,}
artificer = {0: 1, 1: 1, 2: 5, 3: 9, 4: 13, 5: 17,}
halfCaster = {1: 2, 2: 5, 3: 9, 4: 13, 5: 17,}
warlock = {0: 1, 1: 1, 2: 3, 3: 5, 4: 7, 5: 9,}
#i didn't take subclasses into account for fighter and rouge, sorry

Spell_Unlocktable: dict[str, dict[int, int]] = {"Bard": fullCaster, "Cleric": fullCaster, "Druid": fullCaster,
                                                "Sorcerer": fullCaster, "Wizard": fullCaster, "artificer": artificer,
                                                "Paladin": halfCaster, "Ranger": halfCaster, "Warlock": warlock,}

#parsers o7
def ParseBool(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    
    s = str(value).strip().lower()
    if s in trueOptions:
        return True
    if s in False_Options:
        return False
    return bool(s)

def ParseClasses(classes_field: str) -> list[str]:
    if classes_field is None:
        return []
    s = str(classes_field).strip()
    if not s:
        return []
    return [c.strip() for c in s.split(",") if c.strip()]


def GetClassUnlockLvl(class_name: str, spell_level: int) -> int | None:
    table = Spell_Unlocktable.get(class_name)
    if not table:
        return None
    return table.get(spell_level)


#fill the spell tables with the csv columns relevant to it
def ImportSpells(session: Session, csv_path: str, *, chunk_size: int | None = None) -> int:
    inserted = 0
    df_head = pd.read_csv(csv_path, nrows=5)
    required = {"name", "classes", "level", "school", "cast_time", "range", "duration", "verbal",
                "somatic", "material", "material_cost", "description"}
    missing = required - set(df_head.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}. Found: {list(df_head.columns)}")

    reader = pd.read_csv(csv_path, chunksize=chunk_size) if chunk_size else [pd.read_csv(csv_path)]

    for df in reader:
        for _, row in df.iterrows():
            spell_name = str(row["name"]).strip()
            if not spell_name:
                continue

            #add the spell 2 da table
            spell = Spell(
                name=spell_name,
                level=int(row["level"]),
                school=str(row["school"]).strip() if pd.notna(row["school"]) else None,
                cast_time=str(row["cast_time"]).strip() if pd.notna(row["cast_time"]) else None,
                range=str(row["range"]).strip() if pd.notna(row["range"]) else None,
                duration=str(row["duration"]).strip() if pd.notna(row["duration"]) else None,
                description=str(row["description"]).strip() if pd.notna(row["description"]) else None,)

            session.add(spell)
            session.flush()  

            #parse the weird bools, mostly the nan one
            req = SpellRequirements(
                spell_id=spell.id,
                verbal=ParseBool(row["verbal"]),
                somatic=ParseBool(row["somatic"]),
                material=ParseBool(row["material"]),
                material_cost=ParseBool(row["material_cost"]),)
            session.add(req)
            
            #parse the classes since they come in a comma delinated string
            for class_name in ParseClasses(row["classes"]):  
                unlock_level = GetClassUnlockLvl(class_name, spell.level)
                if unlock_level is None:
                    continue

                #add the spell requirements
                session.add(
                    SpellClassRequirement(
                        spell_id=spell.id,
                        class_name=class_name,
                        class_unlock_level=unlock_level,
                    )
                )

            inserted += 1
            
        #commit everything
        session.commit()

    return inserted