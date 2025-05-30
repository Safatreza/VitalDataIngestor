from src.utils.mock_data_generator import MockDataGenerator
import os

def main():
    print("Creating MockDataGenerator instance...")
    generator = MockDataGenerator()
    
    print("\nGenerating test dataset...")
    output_file = 'test_data.csv'
    generator.generate_dataset(
        num_patients=2,
        duration_hours=1,
        output_file=output_file,
        abnormal_probability=0.2
    )
    
    print(f"\nChecking if file was created: {os.path.exists(output_file)}")
    if os.path.exists(output_file):
        print(f"File size: {os.path.getsize(output_file)} bytes")
        with open(output_file, 'r') as f:
            print("\nFirst few lines of the file:")
            for i, line in enumerate(f):
                if i < 5:  # Print first 5 lines
                    print(line.strip())
                else:
                    break

if __name__ == '__main__':
    main() 