#i'm declaring my classes here, and they connect to my database using the ORM logic (bc it is, simply. easier.)
#these are based off my ERD logic
#everything is no longer camel case now bc i didn't realize it was really inconvienent to double quote in sql when you want to see a table otherwise
#refrences: https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/table_config.html

from __future__ import annotations
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Spell(Base):
    __tablename__ = "spells"

    #these are all mapped_column() instead of mapped() bc i wanted to keep them at a specific variable length, similar to the ERD
    #referenced from this page: https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    level: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    school: Mapped[Optional[str]] = mapped_column(String(100))
    cast_time: Mapped[Optional[str]] = mapped_column(String(50))
    range: Mapped[Optional[str]] = mapped_column(String(50))
    duration: Mapped[Optional[str]] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)

    #one 2 one relationship (indicated by the uselist)
    requirements: Mapped["SpellRequirements"] = relationship(
        back_populates="spell", uselist=False, cascade="all, delete-orphan"
    )

    #one 2 many relationship
    class_requirements: Mapped[List["SpellClassRequirement"]] = relationship(
        back_populates="spell", cascade="all, delete-orphan"
    )

    #we out here preventing duplicates since we can have multiple spell requirements
    __table_args__ = (
        UniqueConstraint("name", "level", name="uniqueSpell"),
    )

    def __str__(self):
        return f"{self.name} (Level {self.level})"


#the rest of these are just kinda the same logic as above
class SpellRequirements(Base):
    __tablename__ = "spell_requirements"

    #using a foreign key as a primary key here
    #the cascade is so that if a spell gets deleted so does the requirements.
    #i read that setting the default bool to false on mapped is better for csv imports, so i'm using it
    spell_id: Mapped[int] = mapped_column(
        ForeignKey("spells.id", ondelete="CASCADE"),
        primary_key=True
    )
    verbal: Mapped[bool] = mapped_column(Boolean, default=False)
    somatic: Mapped[bool] = mapped_column(Boolean, default=False)
    material: Mapped[bool] = mapped_column(Boolean, default=False)
    material_cost: Mapped[bool] = mapped_column(Boolean, default=False)

    spell: Mapped[Spell] = relationship(back_populates="requirements")


class SpellClassRequirement(Base):
    __tablename__ = "spell_class_requirements"

    #changed this from the ERD to have its own id for easier deletion if needed
    #still importing the spell id though
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spell_id: Mapped[int] = mapped_column(
        ForeignKey("spells.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    class_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    class_unlock_level: Mapped[int] = mapped_column(Integer, nullable=False)
    spell: Mapped[Spell] = relationship(back_populates="class_requirements")

    __table_args__ = (
        UniqueConstraint("spell_id", "class_name", name="unique_spell_class"),
    )


#a new update to the ERD is updated multiclassing, since TECHNICALLY you can have more than two classes
#so now theres two tables instead of one to support this
class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    classes: Mapped[List["CharacterClass"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )

    spells: Mapped[List["CharacterSpell"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )

    #this is to calculate the characters total levels so they don't go over lvl 20
    @property
    def total_level(self) -> int:
        return sum(c.class_level for c in self.classes)

    def __str__(self):
        return self.name

class CharacterClass(Base):
    __tablename__ = "character_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    class_name: Mapped[str] = mapped_column(String(100), index=True)
    class_level: Mapped[int] = mapped_column(Integer, default=1)
    spellcasting_ability: Mapped[int] = mapped_column(Integer, default=1)
    character: Mapped[Character] = relationship(back_populates="classes")

    __table_args__ = (
        UniqueConstraint("character_id", "class_name", name="unique_char_class"),
    )


class CharacterSpell(Base):
    __tablename__ = "character_spells"

    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        primary_key=True
    )
    spell_id: Mapped[int] = mapped_column(
        ForeignKey("spells.id", ondelete="CASCADE"),
        primary_key=True
    )
    is_prepared: Mapped[bool] = mapped_column(Boolean, default=False)
    character: Mapped[Character] = relationship(back_populates="spells")
    spell: Mapped[Spell] = relationship()

Index("ix_spells_level_school", Spell.level, Spell.school)