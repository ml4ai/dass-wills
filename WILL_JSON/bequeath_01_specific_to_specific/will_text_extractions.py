from schemas.model.te import (
    te_text_extractions
)


def make_instance():

    extractions = te_text_extractions.TETextExtractions(

        entities=
    )

    return extractions


if __name__ == "__main__":
    the_extractions = make_instance()

    print('-'*30, 'Pretty-print the extractions')
    print(the_extractions.to_str())

    print('-'*30, "to_dict():")
    extractions_dict = the_extractions.to_dict()
    print(extractions_dict)