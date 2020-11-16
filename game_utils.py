import csv


class GameStatistic:
    """
    Class for management and save to csv file the game statistic such as current_location, current_experience and
    current_date
    """
    def __init__(self):
        self.statistic = []
        self.output_csv_path = 'dungeon.csv'
        self.field_names = ['current_location', 'current_experience', 'current_date']

    def put(self, current_location, current_experience, current_date):
        """
        Put current statistic to dictionary
        """
        self.statistic.append((current_date, current_location, current_experience))

    def save_to_csv(self):
        """
        Save the dictionary with statistic to csv file
        """
        with open(self.output_csv_path, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(self.field_names)
            csv_writer.writerows(self.statistic)
