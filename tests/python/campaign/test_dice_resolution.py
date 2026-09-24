from mordheim_campaign.ui.components.dice_resolution import roll_d6


def test_roll_d6_returns_requested_number_of_valid_dice():
    dice = roll_d6(100)
    assert len(dice) == 100
    assert all(1 <= value <= 6 for value in dice)
