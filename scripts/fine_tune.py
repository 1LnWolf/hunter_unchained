#!/usr/bin/env python3
import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", required=True)
    parser.add_argument("--model_name", default="mistralai/Mistral-7B-v0.1")
    parser.add_argument("--output_dir", default="./fine_tuned")
    args = parser.parse_args()

    dataset = load_dataset("json", data_files=args.data_path, split="train")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(args.model_name, load_in_8bit=True, device_map="auto")
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16, lora_alpha=32, target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)

    def tokenize_function(examples):
        prompts = [f"### Instruction:\n{i}\n\n### Response:\n" for i in examples["instruction"]]
        targets = examples["output"]
        mi = tokenizer(prompts, truncation=True, max_length=512, padding="max_length")
        lb = tokenizer(targets, truncation=True, max_length=512, padding="max_length")
        mi["labels"] = lb["input_ids"]
        return mi

    tokenized = dataset.map(tokenize_function, batched=True)
    collator = DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        logging_steps=10,
        save_steps=100,
        learning_rate=2e-4,
        fp16=True,
        report_to="none",
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized, data_collator=collator)
    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

if __name__ == "__main__":
    main()