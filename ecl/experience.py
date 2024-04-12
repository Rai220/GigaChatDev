import os
import time
from graph import Graph, Node, Edge
import sys
import openai
import numpy as np
from codes import Codes
from utils import get_easyDict_from_filepath,OpenAIModel,log_and_print_online
from embedding import OpenAIEmbedding
sys.path.append(os.path.join(os.getcwd(),"ecl"))
class Shortcut:
    def __init__(self, sourceMID, targetMID, valueGain,instructionStar,edgeIDPath):
        self.sourceMID = sourceMID
        self.targetMID = targetMID
        self.valueGain = valueGain
        self.embedding  = None
        self.instructionStar = instructionStar
        self.edgeIDPath = edgeIDPath

    def __str__(self):
        return "{} -> {}  valueGain={:.6f} len(instructionPath)={} instructionStar={}".format(self.sourceMID, self.targetMID, self.valueGain, len(self.edgeIDPath), self.instructionStar[:100].replace("\n", ""))

class Experience:
    def __init__(self, graph: Graph, directory: str):
        cfg = get_easyDict_from_filepath("./ecl/config.yaml")
        self.graph: Graph = graph
        self.directory = directory
        self.threshold = cfg.experience.threshold
        self.upperLimit = cfg.experience.upper_limit
        self.experiences = []

        self.model = OpenAIModel(model_type="gpt-3.5-turbo-16k")
        self.embedding_method = OpenAIEmbedding()

        for edge in self.graph.edges:
            node = self.graph.nodes[edge.targetMID]
            node.degree += 1
        assert len(self.graph.edges) * 1 == sum([self.graph.nodes[mid].degree for mid in self.graph.nodes.keys()]) # unidirectional

        for mid in self.graph.nodes.keys():
            node = self.graph.nodes[mid]
            node.value = 1.0

    def reap_zombie(self):

        pathNodes, pathEdges = self.graph.find_shortest_path()

        zombieEdges = [edge for edge in self.graph.edges if edge not in pathEdges]
        zombieNodes = [self.graph.nodes[mid] for mid in self.graph.nodes.keys() if mid not in pathNodes]
        log_zombieedges = "ZOMBIE EDGES: \n"
        log_zombienodes = "ZOMBIE NODES: \n"
        for edge in zombieEdges:
            self.graph.edges.remove(edge)
            log_zombieedges += "Zombie Edge {} -> {} Removed\n".format(edge.sourceMID, edge.targetMID)
        log_and_print_online(log_zombieedges)

        for node in zombieNodes:
            del self.graph.nodes[node.mID]
            log_zombienodes += "Zombie Node {} Removed\n".format(node.mID)
        log_and_print_online(log_zombienodes)

    def estimate(self):
        if len(self.graph.edges) == 0:
            return

        for mid in self.graph.nodes.keys():
            node = self.graph.nodes[mid]
            if len(node.code) == 0:
                node.value *= 0.0

        log_and_print_online()

        vn = self.graph.nodes[self.graph.edges[-1].targetMID]
        # print(vn.mID, "...")

        for mid in self.graph.nodes.keys():
            # print(mid)
            vi = self.graph.nodes[mid]
            vi.value = self._pairwise_estimate(vi, vn)

        log_and_print_online("Init value:"+ str({mid: self.graph.nodes[mid].value for mid in self.graph.nodes.keys()})+"\n\nEstimated value:"+str({mid: self.graph.nodes[mid].value for mid in self.graph.nodes.keys()}))

    def get_cosine_similarity(self, embeddingi, embeddingj):
        embeddingi = np.array(embeddingi)
        embeddingj = np.array(embeddingj)
        cos_sim = embeddingi.dot(embeddingj) / (np.linalg.norm(embeddingi) * np.linalg.norm(embeddingj))
        return cos_sim

    def _pairwise_estimate(self, vi: Node, vj: Node):

        if vi.value == 0.0:
            return 0.0

        pathNodes, pathEdges = self.graph.find_shortest_path(vi.mID, vj.mID)
        distance_weight = 1.0 / len(pathEdges) if len(pathEdges) != 0 else 1.0

        codes = Codes(vi.code)
        codes._rewrite_codes()
        (exist_bugs_flag, test_reports) = codes._run_codes()
        compile_weight = 0.0 if exist_bugs_flag else 1.0

        if compile_weight == 0.0:
            return 0.0

        maximum_degree = max([self.graph.nodes[mid].degree for mid in self.graph.nodes.keys()])
        degree_weight = vi.degree * 1.0 / maximum_degree

        if degree_weight == 0.0:
            return 0.0

        start_time = time.time()
        vi_code_emb = self.embedding_method.get_code_embedding(vi.code) if vi.embedding is None else vi.embedding
        if vi.embedding is None:
            end_time =time.time()
            log_and_print_online("DONE:get node embedding\ntime cost:{}\n".format(end_time-start_time))
        vi.embedding = vi_code_emb
        
        start_time = time.time()
        vj_code_emb = self.embedding_method.get_code_embedding(vj.code) if vj.embedding is None else vj.embedding
        if vj.embedding is None:
            end_time =time.time()
            log_and_print_online("DONE:get node embedding\ntime cost:{}\n".format(end_time-start_time))
        vj.embedding = vj_code_emb
        code_code_cos_sim = self.get_cosine_similarity(vi_code_emb, vj_code_emb)

        if code_code_cos_sim == 0.0:
            return 0.0

        filenames = os.listdir(self.directory)
        filename = [filename for filename in filenames if filename.endswith(".prompt")][0]
        task_prompt = open(os.path.join(self.directory, filename), "r").read().strip()
        start_time = time.time()
        task_emb = self.embedding_method.get_text_embedding(task_prompt) if self.graph.task_embedding is None else self.graph.task_embedding
        if self.graph.task_embedding is None:
            end_time =time.time()
            log_and_print_online("DONE:get task prompt embedding\ntime cost:{}\n".format(end_time-start_time))
        self.graph.task = task_prompt
        self.graph.task_embedding = task_emb
        code_text_cos_sim = self.get_cosine_similarity(vi_code_emb, task_emb)

        if code_text_cos_sim == 0.0:
            return 0.0

        assert distance_weight >= 0.0 and distance_weight <= 1.0
        assert compile_weight >= 0.0 and compile_weight <= 1.0
        assert degree_weight >= 0.0 and degree_weight <= 1.0

        distance = vj.version - vi.version

        if distance == 0:
            return 1
        else:
            return code_code_cos_sim * 1.0 / distance * code_text_cos_sim * compile_weight * degree_weight
        #return distance_weight * compile_weight * degree_weight

    def get_transitive_closure(self):
        def print_matrix(matrix):
            for nodei in matrix.keys():
                for nodej in matrix.keys():
                    print(matrix[nodei][nodej], end=" ")
                print()
            print()

        # Warshall Algorithm
        matrix = {}
        for mid1 in self.graph.nodes:
            for mid2 in self.graph.nodes:
                if mid1 not in matrix.keys():
                    matrix[mid1] = {}
                matrix[mid1][mid2] = 0
        # print_matrix(matrix)

        pathNodes, pathEdges = self.graph.find_shortest_path()
        for edge in pathEdges:
            matrix[edge.sourceMID][edge.targetMID] = 1
        print("Init Adjacent Matrix:")
        print_matrix(matrix)

        for nodek in matrix.keys():
            for nodei in matrix.keys():
                for nodej in matrix.keys():
                    if matrix[nodei][nodej] == 1 or (matrix[nodei][nodek] == 1 and matrix[nodek][nodej] == 1):
                        matrix[nodei][nodej] = 1
        print("Transitive Closure:")
        print_matrix(matrix)

        return matrix

    def extract_thresholded_experiences(self):
        if len(self.graph.edges) == 0:
            return []
        if len(self.graph.nodes) < 2:
            return []
        assert len(self.graph.nodes.keys()) >= 2
        matrix = self.get_transitive_closure()
        
        experiences = []
        pathNodes, _ = self.graph.find_shortest_path()
        for id1 in pathNodes:
            for id2 in pathNodes:
                valueGain = self.graph.nodes[id2].value - self.graph.nodes[id1].value
                flag0 = id1 != id2
                flag1 = self.graph.exists_edge(id1, id2) == False
                flag2 = matrix[id1][id2] == 1
                flag3 = valueGain >= self.threshold

                code_lines = [line.lower().strip() for line in self.graph.nodes[id2].code.split("\n")]
                flag4 = not ("pass".lower() in code_lines or "TODO".lower() in code_lines)

                if flag0 and flag1 and flag2 and flag3 and flag4:
                    _, edges = self.graph.find_shortest_path(uMID=id1, vMID=id2)
                    edgeIDPath = [edge.edgeId for edge in edges]
                    sourcecode=self.graph.nodes[id1].code
                    targetcode=self.graph.nodes[id2].code
                    shortcut = Shortcut(sourceMID=id1, targetMID=id2, valueGain=valueGain,instructionStar="", edgeIDPath=edgeIDPath)
                    experiences.append(shortcut)

        experiences = sorted(experiences, key=lambda item: item.valueGain, reverse = True)

        if len(experiences) > self.upperLimit:
            log_and_print_online("{} experieces truncated.".format(len(experiences) - self.upperLimit))
            experiences = experiences[:self.upperLimit]

        prompt_template0 = """Предоставьте подробные инструкции для создания следующего кода:
{targetcode}

Инструкции должны охватывать следующее:

Модули и классы:
- Перечислите необходимые модули.
- Подробно опишите классы, их атрибуты и методы внутри этих модулей.
- Опишите назначение и функционирование каждого класса.

Структуры данных:
- Определите необходимые структуры данных.
- Опишите их названия, атрибуты и операции.

Основной поток программы:
- Опишите основное развитие программы.
- Выделите последовательность инициализации и вызова других модулей, классов и методов в основном файле (например, main.py).
- Уточните логическую последовательность во время выполнения.

Ввод и вывод:
- Укажите метод получения ввода программы, будь то от пользователей или внешних источников.
- Раскройте предполагаемые выходные данные или действия программы.

Обработка исключений:
- Инструкции по управлению возможными ошибками или исключениями во время выполнения для обеспечения стабильности и надежности.

Внешние библиотеки и зависимости:
- Явно перечислите необходимые внешние библиотеки или зависимости, их версии и функциональность.

Пожалуйста, выведите инструкции напрямую."""

        prompt_template1 = """Пожалуйста, предоставьте подробные инструкции о том, как осуществить переход от начальной версии кода, представленной исходным кодом, к конечной версии, указанной целевым кодом.

        Исходный код:
        {sourcecode}

        Целевой код:
        {targetcode}

Инструкции должны включать в себя:

Модули и классы: Подробно опишите модули, которые должны быть включены, а также имена, атрибуты и операции любых классов, которые должны быть добавлены или изменены. Кроме того, опишите предполагаемую функцию и полезность этих новых или измененных классов.

Структуры данных: Четко определите любые структуры данных, которые требуют введения или изменения, разъяснив их имена, атрибуты и функциональность.

Основной поток программы: Опишите основную последовательность операций программы, выделив процедуры для инициализации и вызова других модулей, классов и методов в основном файле (например, main.py). Опишите логическую последовательность выполнения программы.

Ввод и вывод: Определите методологию получения ввода программой, будь то от пользователей или внешних источников данных. Также опишите предполагаемые выходы или поведение приложения.

Обработка исключений: Предоставьте руководство по управлению возможными несоответствиями или исключениями, которые могут возникнуть во время работы программного обеспечения, обеспечивая его устойчивость и надежность.

Внешние библиотеки и зависимости: Если реализация требует внешних библиотек или зависимостей, явно укажите их имена, версии и соответствующие цели."""


        for shortcut in experiences:
            sourcecode = self.graph.nodes[shortcut.sourceMID].code
            targetcode = self.graph.nodes[shortcut.targetMID].code
            if sourcecode == "":
                prompt = prompt_template0.replace("{targetcode}", targetcode)
                response = self.model.run(messages=[{"role": "system", "content": prompt}])
                print("instructionstar generated")
            else:
                prompt = prompt_template1.replace("{sourcecode}", sourcecode).replace("{targetcode}", targetcode)
                response = self.model.run(messages=[{"role": "system", "content": prompt}])
                print("instructionstar generated")
            shortcut.instructionStar = response["choices"][0]["message"]["content"]
        output = "Sorted-and-Truncated Experiences (with instructionStar):"

        self.experiences = experiences
        for experience in experiences:
            output += str(experience)
        log_and_print_online(output)
        log_and_print_online("[Conclusion]:\nprompt_tokens:{}, completion_tokens:{}, total_tokens:{}".format(self.model.prompt_tokens,self.model.completion_tokens,self.model.total_tokens))
        log_and_print_online("[Conclusion]:\ntext_prompt_tokens:{}, text_total_tokens:{}\ncode_prompt_tokens:{}, code_total_tokens:{}\nprompt_tokens:{}, total_tokens:{}".format(self.embedding_method.text_prompt_tokens,
                                                                                                                                                                                self.embedding_method.text_total_tokens,
                                                                                                                                                                                self.embedding_method.code_prompt_tokens,
                                                                                                                                                                                self.embedding_method.code_total_tokens,
                                                                                                                                                                                self.embedding_method.prompt_tokens,
                                                                                                                                                                                self.embedding_method.total_tokens))
           


        return experiences
    def to_dict(self):
        merged_data = []
        for index, ex in enumerate(self.experiences):
            merged_data.append(ex.__dict__)
        return merged_data
