import json
from time import sleep
from typing import List
import requests


KEYWORDS = ["software", "engineering", "gender", "diversity"]
FIELDS_OF_STUDY = "Computer Science"
QUERY_INFO_BY_KEYWORDS = ["url", "title", "abstract", "authors", "year", "publicationTypes", "venue"]
QUERY_INFO_ABOUT_A_PAPER = ["url", "title", "abstract", "authors", "year", "publicationTypes", "citations",
                            "references", "citations.fieldsOfStudy"]
SEEDING_PAPER_DIR = "seed papers"
SNOWBALLING_PAPER_DIR = "snowballing papers"


class SemanticScholarQueryHelper:
    def __init__(self) -> None:
        self._sesson = requests.session()
        self._api = 'http://api.semanticscholar.org/graph/v1/paper'

    def _get(self, url: str, save_path: str = None) -> str:  # json str
        '''
        Returns the json str that contains the metadata of papers.

                Parameters:
                        url (str): query to semantic scholar
                        save_path (str): path to save the json file

                Returns:
                        response.json() (str): json str
        '''
        try:
            print(f'querying {url}')
            response = self._sesson.get(url, timeout=30)

            if save_path:
                with open(save_path, 'w') as f:
                    json.dump(response.json(), f)

            # Semantic Scholar: use the API endpoint up to 100 requests per 5 minutes
            sleep(3.5)

            return response.json()

        except Exception as e:
            print(e)

    def get_top_n_paper_ids(self, n: int, keywords: List[str], field_of_study: str, save_path: str = None) -> List[str]:
        '''
        Returns the paper ids of top n papers queried by keywords and fields of study

                Parameters:
                        n (int): top n papers from the query results
                        keywords (list[str]): a list of search keywords
                        field_of_study (str) study field of paper.
                            More info about field of study: https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper_search
                        save_path (str): path to save the json files

                Returns:
                        paper_ids (List[str]): paper ids
        '''
        url = f'{self._api}/search?query={"+".join(keywords)}&offset=10&limit={n}&fieldsOfStudy={field_of_study}&fields={",".join(QUERY_INFO_BY_KEYWORDS)}'
        top_n_papers_json = self._get(url, save_path)

        # get paper ID s
        paper_ids = []
        for paper in top_n_papers_json['data']:
            paper_ids.append(paper['paperId'])

        return paper_ids

    def get_metadata(self, paper_id: str, query_parameters: List[str], save_path: str = None) -> str:  # json str
        '''
        Returns a json str that contains the metadata of a specific paper based on specified parameters

                Parameters:
                        paper_id (str): paper id
                        query_parameters (list[str]): a list of attributes about the paper to be queried.
                                More info about query parameters: https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper
                        save_path (str): path to save the json files

                Returns:
                        response.json (str): json str of the paper
        '''
        url = f'{self._api}/{paper_id}?fields={",".join(query_parameters)}'
        return self._get(url, save_path)


class SeedPaper:
    def __init__(self, id: str, query: SemanticScholarQueryHelper) -> None:
        self._id = id
        self._query = query

        save_path = f'./output/{SEEDING_PAPER_DIR}/{self._id}.json'
        metadata = self._query.get_metadata(paper_id=self._id, query_parameters=QUERY_INFO_ABOUT_A_PAPER,
                                            save_path=save_path)

        self._citations = [p['paperId'] for p in metadata['citations']]
        self._references = [p['paperId'] for p in metadata['references']]

    @property
    def citations(self):
        return self._citations

    @property
    def references(self):
        return self._references

    # backward and forward
    def snowballing(self):
        # backward
        for id in self.references:
            save_path = f'./output/{SNOWBALLING_PAPER_DIR}/{id}.json'
            self._query.get_metadata(paper_id=id, query_parameters=QUERY_INFO_ABOUT_A_PAPER,
                                     save_path=save_path)  # ignore return val
        # forward
        for id in self.citations:
            save_path = f'./output/{SNOWBALLING_PAPER_DIR}/{id}.json'
            self._query.get_metadata(paper_id=id, query_parameters=QUERY_INFO_ABOUT_A_PAPER,
                                     save_path=save_path)  # ignore return val


if __name__ == "__main__":
    db_query = SemanticScholarQueryHelper()
    # Get paper ids of the top n papers from Semantic Scholar by keywords and fields of study
    TOP_N_PAPERS = 5
    top_n_save_path = f'./output/top_{TOP_N_PAPERS}_papers_about_{"_".join(KEYWORDS)}.json'
    papers = [SeedPaper(p, db_query) for p in
              db_query.get_top_n_paper_ids(TOP_N_PAPERS, KEYWORDS, FIELDS_OF_STUDY, top_n_save_path)]
    # Do snowballing with the top n papers
    for p in papers:
        p.snowballing()
