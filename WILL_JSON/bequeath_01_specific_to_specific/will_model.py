from schemas.model.wm import (
    wm_asset,
    wm_directive_bequeath,
    wm_person,
    wm_will_model
)


def make_instance():

    # Testator

    testator_john_doe = wm_person.WMPerson(
        name="John Doe",
        id="0x1234"
    )

    # Witnesses

    # witness_jack_doe = wm_person.WMPerson(
    #     name="Jack Doe",
    #     id="0x2345"
    # )
    #
    # witness_jane_doe = wm_person.WMPerson(
    #     name="Jane Doe",
    #     id="0x3456"
    # )

    # Beneficiaries

    beneficiary_tom_doe = wm_person.WMPerson(
        name="Tom Doe",
        id="0x4567"
    )

    beneficiary_mary_hoover = wm_person.WMPerson(
        name="Mary Hoover",
        id="0x5678"
    )

    # Assets

    asset_red_car = wm_asset.WMAsset(
        name="red car",
        id="0x6789"
    )

    asset_vacuum_cleaner = wm_asset.WMAsset(
        name="vacuum cleaner",
        id="0x7890"
    )

    # Directives

    directive_bequeath_car_to_tom = wm_directive_bequeath.WMDirectiveBequeath(
        beneficiaries=[beneficiary_tom_doe],
        assets=[asset_red_car]
    )

    directive_bequeath_vacuum_to_mary = wm_directive_bequeath.WMDirectiveBequeath(
        beneficiaries=[beneficiary_mary_hoover],
        assets=[asset_vacuum_cleaner]
    )

    # The Will Model (top-level structure)

    model = wm_will_model.WMWillModel(
        _date="2023-09-14",
        text="I, John Doe, bequeath my red car to Tom Doe and my vacuum cleaner to Mary Hoover",
        testator=testator_john_doe,
        # witnesses=[witness_jack_doe, witness_jane_doe],
        directives=[directive_bequeath_car_to_tom, directive_bequeath_vacuum_to_mary]
    )

    return model


if __name__ == "__main__":
    the_model = make_instance()

    print('-'*30, 'Pretty-print the model:')
    print(the_model.to_str())

    print('-'*30, 'to_dict():')
    model_dict = the_model.to_dict()
    print(model_dict)
