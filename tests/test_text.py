import pytest
from app.text import canonical,prepare,segments
def test_two_notations(): assert canonical("за́мок") == "з+амок" and canonical("зам+ок") == "зам+ок"
def test_manual_occurrence_wins(): assert prepare("з+амок и замок",{"замок":"зам+ок"}) == "з+амок и зам+ок"
def test_unicode_and_yo_preserved(): assert prepare("ёж и йод\nмука́") == "ёж и йод\nмук+а"
@pytest.mark.parametrize('bad',["+дом","зам+к","́мир"])
def test_invalid(bad):
 with pytest.raises(ValueError): prepare(bad)
def test_long_no_loss():
 text=("Очень длинное предложение для проверки. "*400).strip(); chunks=segments(text)
 assert len(text)>10000 and " ".join(chunks)==text and all(len(x)<=220 for x in chunks)
