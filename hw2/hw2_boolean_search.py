#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from memory_profiler import profile
import argparse
import codecs


class Index:
    def __init__(self, index_file, enumerated_words):
        with open(index_file, 'r', encoding='utf8') as file:
            self.index = [[] for _ in range(len(enumerated_words.keys()))]
            lines = file.readlines()
            self.documents_number = len(lines)
            for line in lines:
                processed_line = line.split('\t')
                doc_num = int(processed_line[0])
                doc_words = (processed_line[1] + processed_line[2]).rstrip().split(' ')
                self.process_document(doc_words, doc_num, enumerated_words)
            for key in range(len(self.index)):
                self.index[key].sort()

    def process_document(self, doc_words, doc_num, enumerated_words):
        for word in doc_words:
            if word in enumerated_words:
                self.index[enumerated_words[word]].append(doc_num)


class Expression:
    def evaluate(self, index, enumerated_words):
        pass


class AbstractOperation(Expression):
    def __init__(self, ex1, ex2):
        self.ex1 = ex1
        self.ex2 = ex2

    def op_imp(self, x, y):
        pass

    def evaluate(self, index, enumerated_words):
        return self.op_imp(self.ex1.evaluate(index, enumerated_words), self.ex2.evaluate(index, enumerated_words))


class Or(AbstractOperation):

    def op_imp(self, x, y):
        i = j = 0
        result = []
        while i < len(x) and j < len(y):
            if x[i] < y[j]:
                result.append(x[i])
                i += 1
            elif x[i] > y[j]:
                result.append(y[j])
                j += 1
            else:
                result.append(x[i])
                i += 1
                j += 1
        while i < len(x):
            result.append(x[i])
            i += 1
        while j < len(y):
            result.append(y[j])
            j += 1
        return result


class And(AbstractOperation):
    def op_imp(self, x, y):
        i = j = 0
        result = []
        while i < len(x) and j < len(y):
            if x[i] < y[j]:
                i += 1
            elif x[i] > y[j]:
                j += 1
            else:
                result.append(x[i])
                i += 1
                j += 1
        return result


class Var(Expression):
    def __init__(self, value):
        self.value = value

    def evaluate(self, index, enumerated_words):
        return index[enumerated_words[self.value]]


class Parser:
    def __init__(self, used_words):
        self.expression = ''
        self.index = 0
        self.used_words = used_words

    def parse(self, expression):
        self.expression = expression
        self.index = 0
        result = self.parse_or()
        self.expression = ''
        self.index = 0
        return result

    def parse_or(self):
        current = self.parse_and()
        while self.index < len(self.expression):
            if self.expression[self.index] != '|':
                break
            self.index += 1
            next = self.parse_and()
            current = Or(current, next)
        return current

    def parse_and(self):
        current = self.parse_bracket()
        while self.index < len(self.expression):
            if self.expression[self.index] != ' ':
                break
            self.index += 1
            next = self.parse_bracket()
            current = And(current, next)
        return current

    def parse_bracket(self):
        if self.expression[self.index] == '(':
            self.index += 1
            r = self.parse_or()
            self.index += 1
            return r
        return self.get_var()

    def get_var(self):
        i = self.index
        while i < len(self.expression) and (self.expression[i].isalpha() or self.expression[i].isdigit()):
            i += 1
        self.used_words.add(self.expression[self.index:i])
        result = Var(self.expression[self.index:i])
        self.index = i
        return result


class QueryTree:

    def __init__(self, qid, query, used_words):
        self.qid = qid
        self.query = query
        self.tree = Parser(used_words).parse(self.query)

    def search(self, index, enumerated_words):
        return self.tree.evaluate(index.index, enumerated_words)


def binarySearch(arr, l, r, x):
    while l <= r:
        mid = l + (r - l) // 2
        if arr[mid] == x:
            return mid

        elif arr[mid] < x:
            l = mid + 1
        else:
            r = mid - 1
    return -1


class SearchResults:
    def __init__(self):
        self.queries = []
        self.cur_query_num = 1

    def add(self, query_tree):
        self.queries.append(query_tree)
        self.cur_query_num += 1

    def print_submission(self, index, enumerated_words, submission_file):
        docs_num = index.documents_number
        with open(submission_file, 'w') as file:
            file.write('ObjectId,Relevance\n')
            for query_id in range(1, self.cur_query_num):
                result = self.queries[query_id - 1].search(index, enumerated_words)
                for doc_id in range(1, docs_num + 1):
                    object_id = doc_id + (query_id - 1) * docs_num
                    search_result = binarySearch(result, 0, len(result) - 1, doc_id)
                    file.write(f'{object_id},{1 if search_result != -1 else 0}\n')


def enumerate_words(used_words):
    enumerated_words = {}
    idx = 0
    for word in used_words:
        enumerated_words[word] = idx
        idx += 1
    return enumerated_words


def main():
    # Command line arguments.
    parser = argparse.ArgumentParser(description='Homework 2: Boolean Search')
    parser.add_argument('--queries_file', required=True, help='queries.numerate.txt')
    parser.add_argument('--objects_file', required=True, help='objects.numerate.txt')
    parser.add_argument('--docs_file', required=True, help='docs.tsv')
    parser.add_argument('--submission_file', required=True, help='output file with relevances')
    args = parser.parse_args()

    # Build index.

    # Process queries.
    # Process queries.
    search_results = SearchResults()
    used_words = set()
    with codecs.open(args.queries_file, mode='r', encoding='utf-8') as queries_fh:
        for line in queries_fh:
            fields = line.rstrip('\n').split('\t')
            qid = int(fields[0])
            query = fields[1]

            # Parse query.
            query_tree = QueryTree(qid, query, used_words)

            # Search and save results.
            search_results.add(query_tree)

    enumerated_words = enumerate_words(used_words)
    used_words = None
    index = Index(args.docs_file, enumerated_words)
    # Generate submission file.
    search_results.print_submission(index, enumerated_words, args.submission_file)


if __name__ == "__main__":
    main()
