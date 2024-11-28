from collections import defaultdict

class ReagentOptimizer:
    def __init__(self):
        self.experiment_data = {
            1: {"name": "Copper (II) (LR)", "reagents": [{"code": "KR1E", "vol": 850}, {"code": "KR1S", "vol": 300}]},
            2: {"name": "Lead (II) Cadmium (II)", "reagents": [{"code": "KR1E", "vol": 850}, {"code": "KR2S", "vol": 400}]},
            3: {"name": "Arsenic (III)", "reagents": [{"code": "KR3E", "vol": 850}, {"code": "KR3S", "vol": 400}]},
            4: {"name": "Nitrates-N (LR)", "reagents": [{"code": "KR4E", "vol": 850}, {"code": "KR4S", "vol": 300}]},
            5: {"name": "Chromium (VI) (LR)", "reagents": [{"code": "KR5E", "vol": 500}, {"code": "KR5S", "vol": 400}]},
            6: {"name": "Manganese (II) (LR)", "reagents": [{"code": "KR6E1", "vol": 500}, {"code": "KR6E2", "vol": 500}, {"code": "KR6E3", "vol": 300}]},
            7: {"name": "Boron (Dissolved)", "reagents": [{"code": "KR7E1", "vol": 1100}, {"code": "KR7E2", "vol": 1860}]},
            8: {"name": "Silica (Dissolved)", "reagents": [{"code": "KR8E1", "vol": 500}, {"code": "KR8E2", "vol": 1600}]},
            9: {"name": "Free Chlorine", "reagents": [{"code": "KR9E1", "vol": 1000}, {"code": "KR9E2", "vol": 1000}]},
            10: {"name": "Total Hardness", "reagents": [{"code": "KR10E1", "vol": 1000}, {"code": "KR10E2", "vol": 1000}, {"code": "KR10E3", "vol": 1600}]},
            11: {"name": "Total Alkalinity (LR)", "reagents": [{"code": "KR11E", "vol": 1000}]},
            12: {"name": "Orthophosphates-P (LR)", "reagents": [{"code": "KR12E1", "vol": 500}, {"code": "KR12E2", "vol": 500}, {"code": "KR12E3", "vol": 200}]},
            13: {"name": "Mercury (II)", "reagents": [{"code": "KR13E1", "vol": 850}, {"code": "KR13S", "vol": 300}]},
            14: {"name": "Selenium (IV)", "reagents": [{"code": "KR14E", "vol": 500}, {"code": "KR14S", "vol": 300}]},
            15: {"name": "Zinc (II) (LR)", "reagents": [{"code": "KR15E", "vol": 850}, {"code": "KR15S", "vol": 400}]},
            16: {"name": "Iron (Dissolved)", "reagents": [{"code": "KR16E1", "vol": 1000}, {"code": "KR16E2", "vol": 1000}, {"code": "KR16E3", "vol": 1000}, {"code": "KR16E4", "vol": 1000}]},
            17: {"name": "Residual Chlorine", "reagents": [{"code": "KR17E1", "vol": 1000}, {"code": "KR17E2", "vol": 1000}, {"code": "KR17E3", "vol": 1000}]},
            18: {"name": "Zinc (HR)", "reagents": [{"code": "KR18E1", "vol": 1000}, {"code": "KR18E2", "vol": 1000}]},
            19: {"name": "Manganese  (HR)", "reagents": [{"code": "KR19E1", "vol": 1000}, {"code": "KR19E2", "vol": 1000}, {"code": "KR19E3", "vol": 1000}]},
            20: {"name": "Orthophosphates-P (HR) ", "reagents": [{"code": "KR20E", "vol": 850}]},
            21: {"name": "Total Alkalinity (HR)", "reagents": [{"code": "KR21E1", "vol": 1000}]},
            22: {"name": "Fluoride", "reagents": [{"code": "KR22E1", "vol": 1000},{"code": "KR22E2", "vol": 1000}]},
            27: {"name": "Molybdenum", "reagents": [{"code": "KR27E1", "vol": 1000}, {"code": "KR27E2", "vol": 1000}]},
            28: {"name": "Nitrates-N (HR)", "reagents": [{"code": "KR28E1", "vol": 1000}, {"code": "KR28E2", "vol": 2000}, {"code": "KR28E3", "vol": 2000}]},
            29: {"name": "Total Ammonia-N", "reagents": [{"code": "KR29E1", "vol": 850}, {"code": "KR29E2", "vol": 850}, {"code": "KR29E3", "vol": 850}]},
            30: {"name": "Chromium (HR)", "reagents": [{"code": "KR30E1", "vol": 1000},{"code": "KR30E2", "vol": 1000}, {"code": "KR30E3", "vol": 1000}]},
            31: {"name": "Nitrite-N", "reagents": [{"code": "KR31E1", "vol": 1000}, {"code": "KR31E2", "vol": 1000}]},
            34: {"name": "Nickel (HR)", "reagents": [{"code": "KR34E1", "vol": 500}, {"code": "KR34E2", "vol": 500}]},
            35: {"name": "Copper (II) (HR)", "reagents": [{"code": "KR35E1", "vol": 1000}, {"code": "KR35E2", "vol": 1000}]},
            36: {"name": "Sulfate", "reagents": [{"code": "KR36E1", "vol": 1000}, {"code": "KR36E2", "vol": 2300}]},
            40: {"name": "Potassium", "reagents": [{"code": "KR40E1", "vol": 1000}, {"code": "KR40E2", "vol": 1000}]},
            42: {"name": "Aluminum-BB", "reagents": [{"code": "KR42E1", "vol": 1000}, {"code": "KR42E2", "vol": 1000}]}
        }

        self.MAX_LOCATIONS = 16

    def calculate_tests(self, volume_ul, capacity_ml):
        return int((capacity_ml * 1000) / volume_ul)

    def get_location_capacity(self, location):
        return 270 if location < 4 else 140

    def optimize_tray_configuration(self, selected_experiments):
        # Validate experiments
        for exp in selected_experiments:
            if exp not in self.experiment_data:
                raise ValueError(f"Invalid experiment number: {exp}")

        # Check total reagents needed
        total_reagents = sum(len(self.experiment_data[exp]["reagents"]) for exp in selected_experiments)
        if total_reagents > self.MAX_LOCATIONS:
            details = [f"{self.experiment_data[exp]['name']}: {len(self.experiment_data[exp]['reagents'])} reagents" 
                      for exp in selected_experiments]
            raise ValueError(
                f"Total reagents needed ({total_reagents}) exceeds available locations ({self.MAX_LOCATIONS}).\n"
                f"Experiment requirements:\n" + "\n".join(details)
            )

        # Initialize configuration
        config = {
            "tray_locations": [None] * self.MAX_LOCATIONS,
            "results": {},
            "available_locations": set(range(self.MAX_LOCATIONS))
        }

        # Sort experiments by complexity and volume requirements
        sorted_experiments = sorted(
            selected_experiments,
            key=lambda x: (
                len(self.experiment_data[x]["reagents"]),
                max(r["vol"] for r in self.experiment_data[x]["reagents"]),
                -min(r["vol"] for r in self.experiment_data[x]["reagents"])  # Prioritize experiments with smaller min volumes
            ),
            reverse=True
        )

        # Phase 1: Place primary sets
        for exp in sorted_experiments:
            self._place_primary_set(exp, config)

        # Phase 2: Optimize additional sets
        self._optimize_additional_sets(sorted_experiments, config)

        return config

    def _place_primary_set(self, exp, config):
        exp_data = self.experiment_data[exp]
        num_reagents = len(exp_data["reagents"])
        
        # Try to place high-volume reagents in 270mL locations first
        high_volume_reagents = any(r["vol"] > 800 for r in exp_data["reagents"])
        if high_volume_reagents:
            available_270 = [loc for loc in range(4) if loc in config["available_locations"]]
            if len(available_270) >= num_reagents:
                self._place_reagent_set(exp, available_270[:num_reagents], config)
                return

        # Otherwise, find best available locations
        available_locs = sorted(config["available_locations"])
        best_locations = []
        
        # Find optimal locations based on reagent volumes
        for reagent in sorted(exp_data["reagents"], key=lambda r: r["vol"], reverse=True):
            best_loc = None
            best_efficiency = 0
            
            for loc in available_locs:
                if loc not in best_locations:
                    capacity = self.get_location_capacity(loc)
                    tests = self.calculate_tests(reagent["vol"], capacity)
                    efficiency = tests / capacity
                    
                    if efficiency > best_efficiency:
                        best_efficiency = efficiency
                        best_loc = loc
            
            if best_loc is not None:
                best_locations.append(best_loc)
                available_locs.remove(best_loc)

        if len(best_locations) == num_reagents:
            self._place_reagent_set(exp, best_locations, config)
        else:
            raise ValueError(f"Could not find suitable locations for experiment {exp}")

    def _optimize_additional_sets(self, experiments, config):
        while config["available_locations"]:
            # Find experiment with lowest tests
            min_tests_exp = min(
                experiments,
                key=lambda x: config["results"][x]["total_tests"] if x in config["results"] else float('inf')
            )
            
            # Check if additional set would improve total tests
            exp_data = self.experiment_data[min_tests_exp]
            num_reagents = len(exp_data["reagents"])
            
            if len(config["available_locations"]) >= num_reagents:
                # Calculate potential improvement
                available = sorted(config["available_locations"])
                potential_tests = float('inf')
                
                for reagent in exp_data["reagents"]:
                    loc = available[0]
                    capacity = self.get_location_capacity(loc)
                    tests = self.calculate_tests(reagent["vol"], capacity)
                    potential_tests = min(potential_tests, tests)
                
                current_tests = config["results"][min_tests_exp]["total_tests"]
                
                # Only place additional set if it improves total tests significantly
                if potential_tests > current_tests * 0.5:
                    locations = sorted(list(config["available_locations"]))[:num_reagents]
                    self._place_reagent_set(min_tests_exp, locations, config)
                else:
                    # If no significant improvement, stop adding sets
                    break
            else:
                break

    def _place_reagent_set(self, exp_num, locations, config):
        exp = self.experiment_data[exp_num]
        sorted_reagents = sorted(exp["reagents"], key=lambda r: r["vol"], reverse=True)
        placements = []

        for i, reagent in enumerate(sorted_reagents):
            loc = locations[i]
            capacity = self.get_location_capacity(loc)
            tests = self.calculate_tests(reagent["vol"], capacity)
            
            placement = {
                "reagent_code": reagent["code"],
                "location": loc,
                "tests": tests,
                "volume": reagent["vol"]
            }
            placements.append(placement)
            
            config["tray_locations"][loc] = {
                "reagent_code": reagent["code"],
                "experiment": exp_num,
                "tests_possible": tests,
                "volume_per_test": reagent["vol"],
                "capacity": capacity
            }
            config["available_locations"].remove(loc)

        set_tests = min(p["tests"] for p in placements)
        
        if exp_num not in config["results"]:
            config["results"][exp_num] = {
                "name": exp["name"],
                "sets": [],
                "total_tests": 0
            }
        
        config["results"][exp_num]["sets"].append({
            "placements": placements,
            "tests_per_set": set_tests
        })
        config["results"][exp_num]["total_tests"] += set_tests

    def get_available_experiments(self):
        return [{"id": id_, "name": exp["name"]} 
                for id_, exp in self.experiment_data.items()]
