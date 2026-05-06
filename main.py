#Final Project - Fenn Edmonds
#note: some of the variables in here are camel case and some are _ seperated
#everything thats _ indicated means its being stored over in an import table bc its easier to query without camelcase but i like camelcase more LOL

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import IntegrityError
from database import SessionLocal
from classes import Base, Character, CharacterClass, Spell, CharacterSpell, SpellClassRequirement

Classes = ["Bard", "Cleric", "Druid", "Sorcerer", "Wizard", "Paladin", "Ranger", "Warlock", "Artificer"]

#keeping my helper functions up here

def GetMod(score: int) -> int:
    if not score:
        #you should theoretically always have a score but like just in case ig
        return 0
    return (score - 10) // 2


def ShowPrepped(character: Character):
    prepared = [cs for cs in character.spells if cs.is_prepared]
    if not prepared:
        print("No spells prepared.")
        return

    prepared.sort(key=lambda x: (x.spell.level, x.spell.name))
    print("\nPrepared Spells:")
    #i love using kaomoji banners to seperate 
    print("✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
    for cs in prepared:
        print(f"[Lvl {cs.spell.level}] {cs.spell.name}")
    print("✦•┈๑⋅⋯ ⋯⋅๑┈•✦")


#basic list function that lets you pass in your options
def Choose(prompt, options):
    if not options:
        return None
    
    print(prompt)
    print("✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
    for i, opt in enumerate(options, 1):
        print(f"{i}. {opt}")
    while True:
        try:
            choice = int(input("✩ "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("Pick something from the list!")
        except ValueError:
            print("Your input needs to be a number!")


def LimitPrepped(session, character) -> int:
    #query explnation time one:
    #grabs the class lvl and spellcasting ability then ignores all classes that have no spell mod.
    rows = session.query(
        CharacterClass.class_level,
        CharacterClass.spellcasting_ability
    ).filter(
        CharacterClass.character_id == character.id,
        CharacterClass.spellcasting_ability.isnot(None)
    ).all()

    #finding the amount of spells allowed (also works with multiclassing!)
    total = sum(
        lvl + GetMod(ability)
        for lvl, ability in rows
    )

    #if your mod sucks you still get at least one spell
    return max(1, total)



def PreppedCount(session, character) -> int:
    #query explnation time: it litterally just counts the rows in the character spells table for a character
    return session.query(func.count(CharacterSpell.spell_id)).filter_by(
        character_id=character.id,
        is_prepared=True
    ).scalar()



def AvailabilityCheck(session, character, spell) -> bool:
    #query explnation time:
    #joins the character class with whether or not the character is above the level needed to cast the spell in their class
    return session.query(SpellClassRequirement).join(
        CharacterClass,
        and_(
            CharacterClass.class_name == SpellClassRequirement.class_name,
            CharacterClass.character_id == character.id,
            CharacterClass.class_level >= SpellClassRequirement.class_unlock_level
        )
    ).filter(
        SpellClassRequirement.spell_id == spell.id
    ).first() is not None


#now the main ui and character creation functionality :))
def CreateChar(session: Session) -> Character:
    while True:
        name = input("Character name: ").strip()

        if not name:
            print("Name can't be empty")
            continue

        #query explanation time: this query just checks if theres already a char with that name in the database by checking the input against the name column
        existing = session.query(Character).filter_by(name=name).first()
        if existing:
            continue
        
        char = Character(name=name)
        session.add(char)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            print("That character name already exists. Try Another!")
            continue
        break

    while True:
        if char.total_level >= 20:
            print("Your combined level is over 20.")
            break

        charClass = Choose("Choose a class:", Classes)

        #max lvl is mainly for multclassing, obviously its 20 otherwise.
        maxLvl = 20 - char.total_level
        while True:
            try:
                lvl = int(input(f"Level (Max {maxLvl}): "))
                if 1 <= lvl <= maxLvl:
                    break
                print(f"Level must be between 1 and {maxLvl}.")
            except ValueError:
                print("Needs to be a number!")

        while True:
            try:
                ability_score = int(input("Spellcasting ability score (1-20): "))
                if 1 <= ability_score <= 20:
                    break
                print("Score must be between 1 and 20.")
            except ValueError:
                print("Needs to be a number!")

        session.add(CharacterClass(
            character_id = char.id,
            class_name = charClass,
            class_level = lvl,
            spellcasting_ability = ability_score
        ))
        session.commit()

        if char.total_level < 20 and input("Add another class? (y/n): ").lower() != "y":
            break

    return char

def AddSpell(session: Session, character: Character):
    #i'm assuming the character has a class since you have to choose one upon creation but we got that edge case handling
    charClasses = [c.class_name for c in character.classes]
    if len(charClasses) == 0:
        print("You have no class! this should litterally not be possible.")
        return
    elif len(charClasses) == 1:
        classSearch = charClasses[0]
    #for multiclassing
    else:
        selection = Choose("Select class to search spells for:", charClasses)
        classSearch = selection
  
    searchLvl = input("Choose a spell lvl: ").strip()
    if not searchLvl:
        print("Invalid")
        return

    #query explanation time: query to grab spells by class and level, i'd display all of them at once but thats like 500 spells
    query = session.query(Spell).join(SpellClassRequirement).filter(
        SpellClassRequirement.class_name == classSearch
    )
    if searchLvl.isdigit():
        query = query.filter(Spell.level == int(searchLvl))
    spells = query.order_by(Spell.level, Spell.name).all()

    if not spells:
        print(f"No spells found for {classSearch}, idk how you even did that.")
        return

    #the part that actually gives the user the option to view a spell
    while True:
        spellOptions = spells + ["Back"]
        selection = Choose("Choose a spell to view details:", spellOptions)
        if selection == "Back" or not selection:
            return
        spell = selection

        print(f"\n✦•┈๑⋅⋯ ⋯⋅๑┈•✦ {spell.name} (Level {spell.level}) ✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
        print(f"Description: {getattr(spell, 'description', 'No description available.')}")
        print("✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
        confirm = Choose("What would you like to do?", ["Add to Known Spells", "Go Back"])
        
        #double check the char is actually able 2 add the spell they want
        if confirm == "Add to Known Spells":
            if not AvailabilityCheck(session, character, spell):
                print("You need to be a higher level for this spell!")
                continue

            if session.get(CharacterSpell, (character.id, spell.id)):
                print("You already know this spell silly.")
                continue

            session.add(CharacterSpell(character_id=character.id, spell_id=spell.id, is_prepared=False))
            session.commit()
            print(f"{spell.name} added!")
            break

        else:
            continue

#prep ya spells
def PrepSpell(session: Session, character: Character):
    #check the spell can actually be prepped
    if PreppedCount(session, character) >= LimitPrepped(session, character):
        print(f"Prepared spell limit ({LimitPrepped(session, character)}) reached!")
        return
    
    availableSpells = [cs for cs in character.spells if not cs.is_prepared]

    if not availableSpells:
        print("You know no spells!")
        return
    
    availableSpells.sort(key=lambda x: (x.spell.level, x.spell.name))
    options = [f"[Lvl {cs.spell.level}] {cs.spell.name}" for cs in availableSpells]
    options.append("Back")
    selection = Choose("Select a spell to prepare:", options)
    
    if selection == "Back" or not selection:
        return
    
    i = options.index(selection)
    spellToPrep = availableSpells[i]
        
    if spellToPrep.is_prepared:
        print("That spell is already prepared.")
        return
    
    #actually commit the spell to the table
    spellToPrep.is_prepared = True
    session.commit()
    print(f"{spellToPrep.spell.name} prepared.")

#i guess you can also unprep your spells...
def UnprepSpell(session: Session, character: Character):
    #check that you actually have spells to unprepare
    prepared = [cs for cs in character.spells if cs.is_prepared]
    if not prepared:
        print("No spells are currently prepared.")
        return

    prepared.sort(key=lambda x: (x.spell.level, x.spell.name))
    options = [f"[Lvl {cs.spell.level}] {cs.spell.name}" for cs in prepared]
    options.append("Back")

    selection = Choose("Choose spell to unprepare:", options)
    if selection == "Back" or not selection:
        return
    
    #actually unprep the spell by changing the bool in the table.
    i = options.index(selection)
    cs = prepared[i]
    cs.is_prepared = False
    session.commit()
    print(f"{cs.spell.name} unprepared.")

#finally, you can delete a spell from your known list!
def DeleteSpell(session: Session, character: Character):
    if not character.spells:
        print("Character has no spells to delete.")
        return

    #get all your spells
    known_spells = [cs.spell for cs in character.spells]
    known_spells.sort(key=lambda x: (x.level, x.name))
    options = known_spells + ["Back"]
    selection = Choose("Choose spell to delete from character:", options)
    
    if selection == "Back" or not selection:
        return
    
    #actually commit to removing the spell from the table
    spell = selection
    cs = session.get(CharacterSpell, (character.id, spell.id))
    session.delete(cs)
    session.commit()
    print(f"{spell.name} removed from character.")

#finally. the character view menu.
def CharMenu(session: Session, character: Character):
    while True:
        print(f"\n✦•┈๑⋅⋯ ⋯⋅๑┈•✦ {character.name} ✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
        print(f"Total Level: {character.total_level}")
        print(f"Prepared Spells: {PreppedCount(session, character)} / {LimitPrepped(session, character)}")

        choice = Choose("Choose:", [
            "Add spell",
            "Prepare spell",
            "Unprepare spell",
            "Show prepared spells",
            "Delete spell",
            "Back"
        ])

        if choice == "Add spell":
            AddSpell(session, character)
        elif choice == "Prepare spell":
            PrepSpell(session, character)
        elif choice == "Unprepare spell":
            UnprepSpell(session, character)
        elif choice == "Show prepared spells":
            ShowPrepped(character)
        elif choice == "Delete spell":
            DeleteSpell(session, character)
        elif choice == "Back" or choice is None:
            break

def main():
   with SessionLocal() as session:
        while True:
            print("\n✦•┈๑⋅⋯ ⋯⋅๑┈•✦")
            mode = Choose("Welcome!", ["Create Character", "View Character", "Exit"])
            
            if mode == "Create Character":
                char = CreateChar(session)
                CharMenu(session, char)
            elif mode == "View Character":
                chars = session.query(Character).all()
                if not chars:
                    print("No characters found.")
                    continue
                char = Choose("Select Character:", chars)
                if char: CharMenu(session, char)
            else:
                break

if __name__ == "__main__":
    main()