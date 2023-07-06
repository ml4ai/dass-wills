# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------

from typing import List
import json
import pprint


class Entity:
    """
    Data about a reading extraction entity
    """

    @staticmethod
    def from_dict(d):
        identifier = None
        if 'id' in d:
            identifier = d['id']
        texts = None
        if 'texts' in d:
            texts = d['texts']
        entity_type = None
        if 'entity_type' in d:
            entity_type = d['entity_type']
        return Entity(identifier=identifier, texts=texts, entity_type=entity_type)

    def __init__(self, identifier: str, texts: List[str], entity_type: str):
        self.id = identifier
        self.texts = texts
        self.type = entity_type

    def __str__(self):
        return f"<Entity id={self.id}, texts={self.texts}, entity_type={self.type}>"


class Event:
    """
    Top-level Event type
    """

    @staticmethod
    def from_dict(d):
        identifier = None
        if 'id' in d:
            identifier = d['id']
        event_type = None
        if 'type' in d:
            event_type = d['type']
        return Event(identifier=identifier, event_type=event_type)

    def __init__(self, identifier: str, event_type: str):
        self.id = identifier
        self.type = event_type

    def __str__(self):
        return f'<Event id={self.id}, type={self.type}>'


class BequestAsset(Event):
    """
    BequestAsset Event
    """

    @staticmethod
    def from_dict(d):
        testator = None
        if 'Testator' in d:
            testator = d['Testator']
        asset = None
        if 'Asset' in d:
            asset = d['Asset']
        benefactor = None
        if 'Benefactor' in d:
            benefactor = d['Benefactor']
        asset_quantifier = None
        if 'AssetQuantifier' in d:
            asset_quantifier = d['AssetQuantifier']
        bequest_distribution_method = None
        if 'BequestDistributionMethod' in d:
            bequest_distribution_method = d['BequestDistributionMethod']
        identifier = None
        if 'id' in d:
            identifier = d['id']
        event_type = None
        if 'type' in d:
            event_type = d['type']

        return BequestAsset(testator=testator, asset=asset, benefactor=benefactor,
                            asset_quantifier=asset_quantifier, bequest_distribution_method=bequest_distribution_method,
                            identifier=identifier, event_type=event_type)

    def __init__(self, testator: str, asset: str, benefactor: str,
                 asset_quantifier: str = None,
                 bequest_distribution_method: str = None,
                 identifier: str = None, event_type: str = None):
        if event_type is None:
            event_type = "BequestAsset"
        Event.__init__(self, identifier, event_type)
        self.testator = testator
        self.asset = asset
        self.asset_quantifier = asset_quantifier
        self.benefactor = benefactor
        self.bequest_distribution_method = bequest_distribution_method

    def __str__(self):
        return f'<BequestAsset id={self.id}, type={self.type}, testator={self.testator}, asset={self.asset}, asset_quantifier={self.asset_quantifier}, benefactor={self.benefactor}, bequest_distribution_method={self.bequest_distribution_method}>'


class Extractions:
    """

    """

    @staticmethod
    def from_json(filepath: str):
        with open(filepath) as extractions_json:
            data = json.load(extractions_json)
            text = None
            if 'text' in data:
                text = data['text']
            entities = None
            if 'entities' in data:
                entities = data['entities']
            events = None
            if 'events' in data:
                events = data['events']
            return Extractions(text=text, entities=entities, events=events)

    def __init__(self, text: str, entities: List[dict], events: List[dict]):
        self.text = text
        entities_dict = dict()
        for entity_dict in entities:
            entities_dict[entity_dict['id']] = Entity.from_dict(entity_dict)
        self.entities = entities_dict
        events_dict = dict()
        for event_dict in events:
            if event_dict['type'] == 'BequestAsset':
                events_dict[event_dict['id']] = BequestAsset.from_dict(event_dict)
            elif event_dict['type'] == 'Event':
                events_dict[event_dict['id']] = Event.from_dict(event_dict)
        self.events = events_dict

    def pprint(self):
        pprint.pprint(self.text)
        print('Entities')
        for key, entity in self.entities.items():
            print(f'{key}: {entity}')
        # pprint.pprint(self.entities)
        print('Events')
        for key, event in self.events.items():
            print(f'{key}: {event}')
        # pprint.pprint(self.events)


# -----------------------------------------------------------------------------

extractions = Extractions.from_json('WILL_JSON/bequeath_03_all_to_type/will_text_extractions.json')
extractions.pprint()

# -----------------------------------------------------------------------------


