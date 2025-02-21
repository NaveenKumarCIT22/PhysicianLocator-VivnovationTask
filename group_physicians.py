import json
import chromadb.api.client as chroma_api_client
from langchain.docstore.document import Document
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
import random
from logger import setup_logger
import chromadb  # Import chromadb

load_dotenv()

logger = setup_logger('group_physicians_logger', 'group_physicians.log')
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
vectorstore = None


def get_full_name(record: dict) -> str:
    """
    Get the full name of a physician from the record.
    """
    basic = record.get("basic", {})
    first_name = basic.get("first_name", "")
    middle_name = basic.get("middle_name", "")
    last_name = basic.get("last_name", "")
    full_name = f"{first_name} {middle_name} {last_name}".strip()

    auth_first_name = basic.get("authorized_official_first_name", "")
    auth_middle_name = basic.get("authorized_official_middle_name", "")
    auth_last_name = basic.get("authorized_official_last_name", "")
    auth_full_name = f"{auth_first_name} {auth_middle_name} {auth_last_name}".strip(
    )

    if auth_full_name:
        return auth_full_name
    return full_name


def get_org_name(record: dict) -> str:
    """
    Get the organization name from the record.
    """
    return record.get("basic", {}).get("organization_name", "")


def get_proper_name(record: dict) -> str:
    """
    Get the proper name (organization or full name) from the record.
    """
    org_name = get_org_name(record)
    ful_name = get_full_name(record)
    if org_name:
        return org_name, ful_name
    return ful_name, ful_name


def get_specialty(record: dict) -> str:
    """
    Get the specialty of a physician from the record.
    """
    taxonomies = record.get("taxonomies", [])
    specialty = [tax.get("desc") if tax else "" for tax in taxonomies]
    specialty = ", ".join(filter(None, specialty)) if any(
        specialty) else "<unknown>"
    return specialty


def process_physician_jsons(json_list):
    """
    Process a list of JSON objects into LangChain Documents.
    """
    documents = []
    for j in json_list:
        metadata = {}
        org, person = get_proper_name(j)
        metadata["full_name"] = person
        metadata["organization_name"] = org

        addresses = j.get("addresses", [])
        location_address = next(
            (addr for addr in addresses if addr.get("address_purpose") == "LOCATION"), {})
        city = location_address.get("city", "")
        state = location_address.get("state", "")
        address_1 = location_address.get("address_1", "")
        postal_code = location_address.get("postal_code", "")
        metadata["address"] = f"{address_1}, {city}, {state} {postal_code}".strip(
        )

        taxonomies = j.get("taxonomies", [])
        specialties = [tax.get("desc")
                       for tax in taxonomies if tax and tax.get("desc")]
        metadata["specialties"] = ", ".join(specialties)
        org, person = get_proper_name(j)
        specialty = get_specialty(j)
        content = f"{person} is specialized in {specialty} and working in {org}, {j.get('addresses', [{}])[0].get('city', '')}" if org else f"{person} is specialized in {specialty} and located in {j.get('addresses', [{}])[0].get('city', '')}"
        documents.append(Document(page_content=content, metadata=metadata))

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2")

    chroma_api_client.SharedSystemClient.clear_system_cache()

    client = chromadb.EphemeralClient()

    vectorstore = Chroma.from_documents(
        documents, embeddings, collection_name="physicians", client=client)

    logger.info(
        f"Processed {len(documents)} physician JSON objects into LangChain Documents.")
    print(
        f"Processed {len(documents)} physician JSON objects into LangChain Documents.")
    return vectorstore


physician_groups = []


def parse_retrievals(docs: list) -> str:
    """
    Parse the retrieved documents and return the result.
    """
    physician_groups.clear()
    result = "\n-----------------\n".join(doc.page_content for doc in docs)
    physician_groups.extend([doc.metadata for doc in docs])
    logger.info(f"Parsed {len(docs)} retrieved documents.")
    print(f"Parsed {len(docs)} retrieved documents." +
          random.choice(['+', '/', '*', '-']))
    return result


def retrieve_physician_groups(vectorstore, query_physician_name):
    """
    Retrieve the physician groups that a physician is part of.
    """
    chat_model = ChatGroq(model_name="llama-3.3-70b-versatile",
                          temperature=0.25, api_key=GROQ_API_KEY)

    prompt_template = ChatPromptTemplate.from_messages([
        ("system",
         "Your task is to respond in `['<org>', '<org>', ...]` format without (`). Do not say anything else. If you cannot find the answer, respond with `[]`."),
        ("user", """
        You are given the following physician records:
        {physician_data}

        Find the physician groups that physician {input_data} is part of. Return the organization_names[].
        """)
    ])

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    chain = (
        {"physician_data": retriever | parse_retrievals,
            "input_data": RunnablePassthrough()}
        | prompt_template
        | chat_model
        | StrOutputParser()
    )

    result = chain.invoke(query_physician_name)
    logger.info(f"Retrieved physician groups for {query_physician_name}.")
    return result, physician_groups


def extract_all_names(json_list):
    """
    Extract all full names from a list of JSON objects.
    """
    names = set()
    for record in json_list:
        basic = record.get("basic", {})
        first_name = basic.get("first_name", "")
        middle_name = basic.get("middle_name", "")
        last_name = basic.get("last_name", "")
        full_name = f"{first_name} {middle_name} {last_name}".strip()
        if full_name:
            names.add(full_name)

        auth_first_name = basic.get("authorized_official_first_name", "")
        auth_middle_name = basic.get("authorized_official_middle_name", "")
        auth_last_name = basic.get("authorized_official_last_name", "")
        auth_full_name = f"{auth_first_name} {auth_middle_name} {auth_last_name}".strip(
        )
        if auth_full_name:
            names.add(auth_full_name)

    logger.info(f"Extracted {len(names)} full names from JSON objects.")
    return list(names)


def get_groups(physician_data):
    """
    Get the groups that physicians are part of.
    """
    vectorstore = process_physician_jsons(physician_data)
    person_to_groups = {}
    all_physician_groups = []
    for name in extract_all_names(physician_data):
        res, physician_groups = retrieve_physician_groups(vectorstore, name)
        all_physician_groups.extend(physician_groups)
        try:
            groups = eval(res)
            if isinstance(groups, list):
                person_to_groups[name] = groups
            else:
                person_to_groups[name] = []
        except (SyntaxError, NameError, TypeError) as e:
            logger.error(f"Error evaluating result for {name}: {e}")
            continue
    logger.info(f"Retrieved groups for {len(person_to_groups)} physicians.")
    return person_to_groups, all_physician_groups


if __name__ == "__main__":
    physician_data = [
        {
            "created_epoch": "1163605769000",
            "enumeration_type": "NPI-1",
            "last_updated_epoch": "1280769356000",
            "number": "1255403010",
            "addresses": [
                {
                    "country_code": "US",
                    "country_name": "United States",
                    "address_purpose": "LOCATION",
                    "address_type": "DOM",
                    "address_1": "AVE OSVALDO MOLINA #151",
                    "address_2": "SUITE 103",
                    "city": "FAJARDO",
                    "state": "PR",
                    "postal_code": "007383614",
                    "telephone_number": "787-801-0081"
                },
                {
                    "country_code": "US",
                    "country_name": "United States",
                    "address_purpose": "MAILING",
                    "address_type": "DOM",
                    "address_1": "PO BOX 458",
                    "city": "PUERTO REAL",
                    "state": "PR",
                    "postal_code": "007400458"
                }
            ],
            "practiceLocations": [],
            "basic": {
                "first_name": "CARLOS",
                "last_name": "FONTANEZ",
                "middle_name": "AGAPITO",
                "credential": "M.D.",
                "sole_proprietor": "YES",
                "gender": "M",
                "enumeration_date": "2006-11-15",
                "last_updated": "2010-08-02",
                "status": "A",
                "name_prefix": "--",
                "name_suffix": "--"
            },
            "taxonomies": [
                {
                    "code": "207R00000X",
                    "taxonomy_group": "",
                    "desc": "Internal Medicine",
                    "state": "PR",
                    "license": "16110",
                    "primary": True
                }
            ],
            "identifiers": [],
            "endpoints": [],
            "other_names": []
        },

        {
            "created_epoch": "1216215348000",
            "enumeration_type": "NPI-2",
            "last_updated_epoch": "1407337958000",
            "number": "1285898502",
            "addresses": [
                {
                    "country_code": "US",
                    "country_name": "United States",
                    "address_purpose": "LOCATION",
                    "address_type": "DOM",
                    "address_1": "151 AVE OSVALDO MOLINA",
                    "address_2": "SUITE 103",
                    "city": "FAJARDO",
                    "state": "PR",
                    "postal_code": "007384013",
                    "telephone_number": "787-801-0081"
                },
                {
                    "country_code": "US",
                    "country_name": "United States",
                    "address_purpose": "MAILING",
                    "address_type": "DOM",
                    "address_1": "PO BOX 458",
                    "city": "PUERTO REAL",
                    "state": "PR",
                    "postal_code": "007400458",
                    "telephone_number": "787-801-0081"
                }
            ],
            "practiceLocations": [],
            "basic": {
                "organization_name": "CENTRO GERIATRICO DEL ESTE PSC",
                "organizational_subpart": "NO",
                "enumeration_date": "2008-07-16",
                "last_updated": "2014-08-06",
                "status": "A",
                "authorized_official_first_name": "CARLOS",
                "authorized_official_last_name": "FONTANEZ, MD",
                "authorized_official_middle_name": "A",
                "authorized_official_telephone_number": "7873404125",
                "authorized_official_title_or_position": "medico",
                "authorized_official_name_prefix": "Dr.",
                "authorized_official_name_suffix": "Sr.",
                "authorized_official_credential": "16110"
            },
            "taxonomies": [
                {
                    "code": "207RG0300X",
                    "taxonomy_group": "193400000X - Single Specialty Group",
                    "desc": "Internal Medicine, Geriatric Medicine",
                    "state": "PR",
                    "license": "5177",
                    "primary": True
                }
            ],
            "identifiers": [],
            "endpoints": [],
            "other_names": []
        },
    ]

    vectorstore = process_physician_jsons(physician_data)

    for name in extract_all_names(physician_data):
        query_name = name
        print(query_name)
        res, physician_groups = retrieve_physician_groups(
            vectorstore, query_name)
        print("Retrieved Physician Groups:")
        print("----------------------------")
        print(res)
        print("----------------------------")
        print(physician_groups)
        print("----------------------------")
        print(eval(res))
        print("----------------------------")
