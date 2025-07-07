from simpn.reporters import EventLogReporter
from tempfile import NamedTemporaryFile

class Conformance:
    """
    A class that can calculate the conformance of an event log, produced via the EventLogReporter, to a process model, specified as a SimProblem with BPMN prototypes.
    It has methods to calculate the fitness and the precision metrics.
    Fitness and precision are calculated based on the edit distance similarity between traces from the event log and the process model.
    The edit distance similarity between a trace t from the event log and a trace p from the process model is: the lowest number of insertions, deletions, and substitutions needed to transform t into p, divided by max(length of p, length of t).
    The fitness of a trace t from the event log is the highest edit distance similarity between t and any trace p from the process model.
    The fitness of the event log is the average fitness of all traces in the event log.
    The precision is analogously computed as the average fitness of all traces in the process model with respect to the event log.
    Preconditions:
    - we assume that events are in the log in the order of their occurrence in time.
    - the sim_problem must be in its initial state when the Conformance class is instantiated.
    """

    def __init__(self, sim_problem, event_log, separator=",", case_id_column="case_id", task_column="task", sample_duration=1000):
        """
        Initializes the Conformance class with a SimProblem and an event log.

        :param sim_problem: An instance of SimProblem containing the process model.
        :param event_log: The filename of an event log.
        :param separator: The separator used in the event log file (default is comma).
        :param case_id_column: The name of the column in the event log that contains the case IDs (default is "case_id").
        :param task_column: The name of the column in the event log that contains the task labels (default is "task").
        :param sample_duration: The time the simulator will be run to generate traces to calculate the fitness/ precision over (default is 1000).
        """
        self.INITIAL_STATE = "initial state"
        self.sim_problem = sim_problem
        self.sim_problem.store_checkpoint(self.INITIAL_STATE)  # Store the initial state of the process model
        self.event_log = event_log
        self.separator = separator
        self.case_id_column = case_id_column
        self.task_column = task_column
        self.sample_duration = sample_duration
        self.traces_sampled_from_process = self.generate_traces(duration=sample_duration)
        self.sim_problem.restore_checkpoint(self.INITIAL_STATE)  # Restore the initial state after generating traces
        self.traces_extracted_from_log = self.extract_traces(event_log, separator=separator, case_id_column=case_id_column, task_column=task_column)
    
    def extract_traces(self, event_log, separator=",", case_id_column="case_id", task_column="task"):
        """
        Extracts traces from the event log.
        The result is a dictionary of trace -> frequency of occurrence, where each trace is a list of task labels.

        :return: A dictionary of traces with the frequency of their occurrence.
        """
        with open(event_log, 'r') as file:
            header = file.readline().strip().split(separator)
            case_id_index = header.index(case_id_column)
            task_index = header.index(task_column)

            # A dictionary case_id -> list of tasks
            cases = {}

            for line in file:
                if line.strip():
                    parts = line.strip().split(separator)
                    case_id = parts[case_id_index]
                    task = parts[task_index]

                    if case_id not in cases:
                        cases[case_id] = []
                    cases[case_id].append(task)

            # Convert cases to traces
            traces = {}
            for case_id, tasks in cases.items():
                trace = tuple(tasks)
                if trace not in traces:
                    traces[trace] = 0
                traces[trace] += 1

        return traces

    def generate_traces(self, duration=1000):
        """
        Generates traces from the SimProblem's process model.
        The result is a dictionary of trace -> frequency of occurrence, where each trace is a list of task labels.

        :return: A dictionary of traces with the frequency of their occurrence.
        """

        # We can generate traces by simulating the process model, storing the event log in a temporary file, and then extracting the traces from that log.
        with NamedTemporaryFile() as temp_log:            
            reporter = EventLogReporter(temp_log.name, separator=self.separator)
            self.sim_problem.restore_checkpoint(self.INITIAL_STATE)
            self.sim_problem.simulate(duration, reporter)
            temp_log.flush()

            # Now extract traces from the temporary log file
            traces = self.extract_traces(temp_log.name, separator=self.separator)

            # Clean up the temporary file
            temp_log.close()

            return traces

    def edit_distance_similarity(self, trace1, trace2):
        """
        Calculates the edit distance similarity between two traces.
        The edit distance similarity is defined as the lowest number of insertions, deletions, and substitutions needed to transform trace1 into trace2, divided by max(length of trace1, length of trace2).

        :param trace1: A list representing the first trace.
        :param trace2: A list representing the second trace.
        :return: A float representing the edit distance similarity.
        """
        len1 = len(trace1)
        len2 = len(trace2)

        # Create a distance matrix
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            for j in range(len2 + 1):
                if i == 0:
                    dp[i][j] = j
                elif j == 0:
                    dp[i][j] = i
                elif trace1[i - 1] == trace2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = min(dp[i - 1][j] + 1,      # Deletion
                                   dp[i][j - 1] + 1,      # Insertion
                                   dp[i - 1][j - 1] + 1)
        edit_distance = dp[len1][len2]
        max_length = max(len1, len2)
        if max_length == 0:
            return 1.0
        return 1 - (edit_distance / max_length)  # Return similarity as a value

    def calculate_fit(self, from_traces, to_traces):
        """
        Calculates the fitness of a set of traces with respect to another set of traces.
        The fitness is defined as the average similarity of each trace in from_traces to the best matching trace in to_traces.
        :param from_traces: A dictionary of traces with their frequencies.
        :param to_traces: A dictionary of traces with their frequencies.
        :return: A float representing the fitness value.
        """
        fitness_values = []

        for from_trace, from_frequency in from_traces.items():
            max_similarity = 0.0
            for to_trace in to_traces.keys():
                similarity = self.edit_distance_similarity(from_trace, to_trace)
                if similarity > max_similarity:
                    max_similarity = similarity
            fitness_values.append(max_similarity * from_frequency)

        if not fitness_values:
            return 0.0
        return sum(fitness_values) / sum(from_traces.values())

    def calculate_fitness(self):
        """
        Calculates the fitness of the event log with respect to the process model.

        :return: A float representing the fitness value.
        """
        return self.calculate_fit(self.traces_extracted_from_log, self.traces_sampled_from_process)        
    
    def calculate_precision(self):
        """
        Calculates the precision of the event log with respect to the process model.
        :return: A float representing the precision value.
        """
        return self.calculate_fit(self.traces_sampled_from_process, self.traces_extracted_from_log)
