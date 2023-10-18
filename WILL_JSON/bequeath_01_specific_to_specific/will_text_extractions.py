from schemas.model.te import (
    te_entity,
    te_event_bequeath,
    te_text_extractions
)


def make_instance():

    # Entities

    entity_e1 = te_entity.TEEntity(
        id="e1",
        texts=["John Doe", "I", "my"],
        type="Testator"
    )

    entity_e2 = te_entity.TEEntity(
        id="e2",
        texts=["Tom Doe"],
        type="BeneficiaryNamed"
    )

    entity_e3 = te_entity.TEEntity(
        id="e3",
        texts=["Mary Hoover"],
        type="BeneficiaryNamed"
    )

    entity_e4 = te_entity.TEEntity(
        id="e4",
        texts=["red car"],
        type="Asset"
    )

    entity_e5 = te_entity.TEEntity(
        id="e5",
        texts=["vacuum cleaner"],
        type="Asset"
    )

    # Events

    event_v1 = te_event_bequeath.TEEventBequeath(
        id="v1",
        type="BequestAsset",
        testator="e1",
        asset="e4",
        benefactor="e2"
    )

    event_v2 = te_event_bequeath.TEEventBequeath(
        id="v2",
        type="BequestAsset",
        testator="e2",
        asset="e5",
        benefactor="e3"
    )

    # The Text Extractions (top-level structure)

    extractions = te_text_extractions.TETextExtractions(
        _date="2023-09-13",
        text="I, John Doe, bequeath my red car to Tom Doe and my vacuum cleaner to Mary Hoover",
        entities=[entity_e1, entity_e2, entity_e3, entity_e4, entity_e5],
        events=[event_v1, event_v2]
    )

    return extractions


if __name__ == "__main__":
    the_extractions = make_instance()

    print('-'*30, 'Pretty-print the extractions')
    print(the_extractions.to_str())

    print('-'*30, "to_dict():")
    extractions_dict = the_extractions.to_dict()
    print(extractions_dict)