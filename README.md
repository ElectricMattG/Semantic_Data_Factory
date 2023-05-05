# <b>Large Language Models as Teacher Networks in E-Commerce and Search Production Environments</b>

## <b>Overview</b>
<br>
<p>This repo is a multi-threaded, containerized Python application designed for efficient synthesis of textual/tabular data in production environments. The repo also can be used to efficiently produce deeply learnt, vector-embeddings from text, enabling industry standard semantic-search and synthetic data-generation, using state-of-the-art generative pretrained Transformer models (Brown et al., 2020; Radford, Narasimhan, et al., 2018; Radford, Wu, et al., 2018).</p>
<p>Synthetic data generation is important to search and e-commerce, because it allows engineering teams to produce large, annotated training and evaluation sets for common modelling tasks, like retrieval, recommendations, and ranking. Synthesizing data in this manner reduces model development costs, due to the fact that one isn’t overly reliant on annotators, nor time-constrained by productivity levels and task-complexity (see Gilardi et al., 2023 for a comparison between GPT models and crowd-sourced human annotations).</p>
<p>In machine-learning circles, LLMs are often seen as good “teacher” models that can be used to generate synthetic data to train and fine-tune more concise production models for a specific task-domain (Hinton et al., 2015; Magister et al., 2022; West et al., 2022). Stanford’s Alpaca model is a good use-case that illustrates this point clearly by training an instructGPT distillation using GPT3 as the teacher network (Wang et al., 2022).</p>
<p>Embeddings are powerful artefacts that can form the basis of semantic-search indices, zero-shot product/customer classifiers, and provide a representational space for mining customer-product relationships that aren’t immediately apparent using linear methods. As with generative the use-case, the available on-line repo’s don’t provide production ready implementations, but are more POCs for production system components.</p>
<p>This repo offers a multithreading production framework for running large-scale cronjobs that interact with OpenAI’s API endpoints, specifically for tabular-data generation and vector-embedding sampling. The repo offers a simple and useful integration layer for cronjobs that interact with OpenAI’s servers.</p>

<br>

 ## <b>Architecture</b>
 <br>
 <p>The application is deployed as a Kubernetes cronjob with-in a Google Kubernetes Environment (see diagram below). The application is built with a control layer and three core component handlers: <b>APIDataHandler</b>, this is the main component/handler. It has two dependencies that we inject at run-time: <b>APIhandler</b> and <b>PromptHandler</b>. 
 <p>An additional component forms the control layer of the architecture. This component is called the <b>Job Manager</b>. It’s not considered part of the core application, as the core application can run independently from the job manager. Specifically, the job manager interfaces with the application’s public API interface and manages the multithreading logic and data-buffers/queues for the application. </p>
 <br>


 <p align="center"><img src=./images/architecture_1_3.png></img></p>
 <p align="center" style="font-size: 13px"><b>Caption 1</b> <i>Architecture diagram</i>. Injected dependencies are in green. The grouped APIHandlers represent multithreaded logic. Buffers are shown as cylinders. The flow of data during a cronjob is shown as dotted lines. Retry logic for persistent errors is shown in red. Stubbed integrations are stubbed as [FILE I/O]’s.</p>
 <br>
 <p>The details of the core application components are as follow:</p>
 <p><ol>
 <li>The <b>APIDataHandler</b> (main application interface) implements key utilities to handle the API request-response data, to ensure reliable robust data transfer between the application and its integrations—in this repo storage integrations are stubbed as FILE I/Os, while the OpenAI integration is implemented via JSON/HTTPS. Stubbed FILE I/Os can be extended for Google Cloud Storage, Elastic Search, Big-Query, Kafka, as well as Databricks integrations.</li>
 <br>
 <li>The <b>APIHandler</b> (injectable dependency) handles the calls to OpenAI’s server, implements error handling for transient APIErrors, and a retry buffer for persistent errors that are not resolved through exponential backoff.</li>
 <br>
 <li>The <b>PromptHanllder</b> (injectable dependency) handles the input data for synthetic data generation and for embeddings. It provides an interface for the application-data with the query-data, but the handler also enables a prompt-injection framework, so one can also get embeddings for more complex prompt structures, i.e. involving multiple products, or product-customer interactions.</li>
 </ol>
 </p>
 <p></p>
 <br>


 ## <b>Usage</b>
 <br>
 <p>One needs an active OpenAI account with a valid API key to run these jobs. One can register for an account and generate and API key on <a href="https://openai.com/pricing">OpenAI’s website</a>. Any costs accrued when using this repo are for your own expense--you are responsible for your own OpenAI account. No external rate-limit agreements are in-place with OpenAI, so the application is constrained by the native, public <a href="https://platform.openai.com/docs/guides/rate-limits/overview">OpenAI rate-limits.</a></p>
 <p>This application has been tested with python 3.8, 3.9, and 3.10. Please ensure that python venv module is installed to manage the creation of virtual environments. Jobs can be run from within a virtual environment using the following terminal commands within a bash shell.</p>
 <pre style="white-space: pre-wrap;">
 <b>$ git clone git@github.com:ElectricMattG/TAL_DML_Semantic_Data_Factory.git</b>
 <b>$ cd TAL_DML_Semantic_Data_Factory</b>
 <b>$ make install</b>
 <b>$ source ./.venv/bin/activate</b></pre>
 <p>Update your OpenAI api key in the config. One needs to do this to run the application. The configuration section below provides details of the config. The defaults are set to an embedding job for 1500 search queries. Run the tests to check the install and config. Then run the application.</p>
 <pre style="white-space: pre-wrap;">
 <b>$ make test</b>
 <b>$ python -m src.main</b></pre>
 <p>Alternatively, after the install, configuration and tests, one can build a docker image and run a job as a containerised appliaction. Follow the build commands above, and then instead or running the main module, run the docker commands below. Once the job has executed, you can explore the results within the container.</p>
 <pre style="white-space: pre-wrap;">
 <b>$ docker build -t datafactory .</b>
 <b>$ docker run datafactory</b>
 <b>$ docker start "container_id"</b>
 <b>$ docker exec -it "container_id" bash</b></pre>
 <br>   

 ### <b>Configuration</b>
 <br>
 <p>The job is configured from with configuration config.py in the ./src directory of the project.</p>
 <br>

 <p align="center" ><img  src=./images/config_1.svg></img></p>
 <p align="center" ><img  src=./images/config_2.svg></img></p>
 <p align="center" style="font-size: 13px"><b>Caption 2</b> <i>Application configuration</i>. Configuration file with the key paramaters</p>
 <br>

 <p>Config is defined as the following:<ul> 
 <li>workstream – whether the job is generative or embedding,</li>
 <li>account – holds the API key from OpenAI,</li>
 <li>api_performance_data – the directory where the API performance data is saved,</li>
 <li>app – the control settings for the job manager to manage the workstream,</li>
 <li>exponential_backoff – parameters for dealing with transient errors,</li>
 <li>gpt_embedding_params – model config and cost per 1000 tokens,</li>
 <li>gpt_generate_params – model config and cost per 1000 tokens,</li>
 <li>input_data – directory of the input data,</li>
 <li>logging – format, logging level, and output directory,</li> 
 <li>output_data – the directory where the output files will be written,</li> 
 <li>prompt – this is a prompt template that we inject queries/products/customer descriptions into for synthetic data generation,</li> 
 <li>counters – deprecated method for counting queries.</li></ul>
 </p>
 <br>
 <p>The config provides a set of defaults known to produce reliable results in testing. A suggestion is to maintain these defaults, outside of the defaults, other choices have not been fully tested. Changing end-points requires hard-coded changes in the config, or patching in the APIHandler—details are provided elsewhere. This repo implements completion and embedding end-point integration to align with Wang et al., (2022).</p>
 <br>


### <b>Input</b>
 <br>
 <p>Data for processing is provided as a csv file. Where each row in the column is an instance of text: a query, a product title, product description, even a customer review. The first row in the csv contains the headers. The ‘query’ is the column that is processed. Below is an example for Amazon ESCI benchmark dataset: this dataset represents >10k difficult Amazon search queries (Reddy et al., 2022)--the only field required by the application is ‘query’.</p>
 <br>
 <img align="center" src=./images/data_1.svg></img>
 <p align="center" style="font-size: 13px"><b>Caption 3</b> <i>Input Data</i>. A .csv file containing the ESCI dataset for difficult queries. Column headers are in the first row.</p>
 <br>

 ### <b>Output</b> 
 <br>
 <p>For each cronjob a folder is created with the current data-time and a suffix is added depending on the job type: embedding or generative task. Where generative task is to generate synthetic tabular data based on zero-shot learning.</p>

 #### <b>Folder Structure</b> 
 <p>The folder structure for each cronjob contains 4 sub-folders, found within the data folder in the root of the repo:
 <ol>
 <li>The <b>api_performance_data</b> folder. Depending on user config, the job manager will regularly save the api performance data. This application only logs successful API calls; errors, retries and the details of those tasks are available in the logs.</li><br>
 <li>The <b>logs</b> folder. Application logging, where each cronjob has its own log file. Logging-level and format are specified within in the config (see /src/config.py > “logging”).</li><br>
 <li>The <b>model_completions</b> folder. Contains the response data from the api-request. For generate tasks, these will be JSON tables; for embed tasks, these will be JSON tables containing the embedding-vectors.</li></br>
 <li>The <b>unprocessed prompts</b> folder containing a JSON file of all the unprocessed prompts</li><br>
 </ol>
 </p>
 <img align="center" src=./images/folder_1.svg></img>
 <p align="center" style="font-size: 13px"><b>Caption 4</b> <i>Folder structure</i>. A folder is generated for each job. The folder is labelled according to the date time the cronjob kicked-off.</p>
 <br>



## <b>Things you should know about the repo</b>
<br>
<p>The defaults have been well-tested and we have not encountered issues with the pipeline itself. Some errors arise if the prompt gets too complex, the generated output may not adhere to a valid JSON structure; however, this only occurs when the instructions in the prompt get too detailed for a single-prompt. Such detailed types of tasks are better suited to a chat-end point, where the context is built up over a number of separate prompts to adequately prime the Transformer. Our generative workstream is GPT3 text-completion, where we implement a zero-shot JSON data-factory.</p>
<p>Only successful calls to the APIs are tracked in the performance data. Errors are addressed in the logs. So if you had 1000 queries to embed and there are only 995 successful calls, please check the logs for the errors and the unprocessed prompts folder in the output data, then adjust the complexity of the prompt for generative tasks, particularly if there are any invalidJSONErrors. Also keep the number of concurrent workers in a reasonable range, choosing between 5-10 workers when dealing with hundreds and thousands of prompts works well when tested on a 12 core CPU.</p>
<p>It’s easy to determine the cost of a job by running the job on 100 samples and extrapolating from those statistics, which are calculated as part of the job and are available in the logs. For example, to embed 100 000 product titles, where the average length of the product title is 7 tokens, would only cost around $0.26 and is likely to run for 87.7 minutes. With a throughput of 144 tokens/second and an api-latency of around 500 milliseconds, the embedding workstream offers great value for money.</p>
<p>To generate a synthetic query understanding dataset for the ESCI dataset, i.e. 100 000 fully annotated queries (brand, category, bread-crumbs, book vs non-book…), would cost around $264.37 and is likely to run for 22 hours. With a throughput of 163 tokens/second and an api-latency of 114 seconds—bearing in-mind that this is a generative Transformer end-point—the generative workstream offers a competitive solution compared to human annotators (Gilardi et al., 2023).</p>
<p>We strongly suggest spending time with a GPT chat-agent to build and test prompts in the <a href="https://platform.openai.com/playground">OpenAI playground</a>, it gives one the chance to refine a prompt and understand it’s output without incurring costs.</p>
<br>

## <b>Citations</b>
<br>

<p>Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D. M., Wu, J., Winter, C., … Amodei, D. (2020). Language Models are Few-Shot Learners (arXiv:2005.14165). arXiv. https://doi.org/10.48550/arXiv.2005.14165</p>
<p>Gilardi, F., Alizadeh, M., & Kubli, M. (2023). ChatGPT Outperforms Crowd-Workers for Text-Annotation Tasks (arXiv:2303.15056). arXiv. https://doi.org/10.48550/arXiv.2303.15056</p>
<p>Hinton, G., Vinyals, O., & Dean, J. (2015). Distilling the Knowledge in a Neural Network (arXiv:1503.02531). arXiv. https://doi.org/10.48550/arXiv.1503.02531</p>
<p>Magister, L. C., Mallinson, J., Adamek, J., Malmi, E., & Severyn, A. (2022). Teaching Small Language Models to Reason (arXiv:2212.08410). arXiv. https://doi.org/10.48550/arXiv.2212.08410</p>
<p>Radford, A., Narasimhan, K., Salimans, T., & Sutskever, I. (2018). Improving language understanding by generative pre-training.</p>
<p>Reddy, C. K., Màrquez, L., Valero, F., Rao, N., Zaragoza, H., Bandyopadhyay, S., Biswas, A., Xing, A., & Subbian, K. (2022). Shopping Queries Dataset: A Large-Scale ESCI Benchmark for Improving Product Search (arXiv:2206.06588). arXiv. https://doi.org/10.48550/arXiv.2206.06588</p>
<p>Wang, Y., Kordi, Y., Mishra, S., Liu, A., Smith, N. A., Khashabi, D., & Hajishirzi, H. (2022). Self-Instruct: Aligning Language Model with Self Generated Instructions (arXiv:2212.10560). arXiv. https://doi.org/10.48550/arXiv.2212.10560</p>
<p>West, P., Bhagavatula, C., Hessel, J., Hwang, J., Jiang, L., Le Bras, R., Lu, X., Welleck, S., & Choi, Y. (2022). Symbolic Knowledge Distillation: From General Language Models to Commonsense Models. Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, 4602–4625. https://doi.org/10.18653/v1/2022.naacl-main.341</p>
<p></p>

 <br>
 
 ### <b>Examples</b>
 <p></p>
 <br>
 <p align="center" style="font-size: 14px"><b>#1</b> Below is an example of the data from the embedding end-point</p>
 <img align="center" src=./images/embeddings_1.svg></img>
 <br><br>
 <p align="center" style="font-size: 14px"><b>#2</b> Below is an example of the data from the logs</p>
 <img align="center" src=./images/log_1.svg></img>
 <br><br>
 <p align="center" style="font-size: 14px"><b>#3</b> Below is synthetic data generated for difficult queries from the Amazon ESCI dataset.</p>
 <img align="center" src=./images/completion_1.svg></img>
 <br><br>
