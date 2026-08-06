# Urgency Classification Dataset Research

## Purpose

This document investigates suitable datasets for training an urgency classification model for the FireFusion project. The model will classify bushfire-related information into urgency levels such as urgent, not urgent, and not useful.

The research focuses on publicly available datasets, possible label structures, dataset limitations, and whether synthetic or manually annotated data may be required.

## Classification Requirements

The proposed urgency classification model should assign each bushfire-related text item to one of the following categories:

- **Urgent:** Information that requires immediate attention or action, such as an active fire threat, evacuation warning, trapped people, injuries, or immediate danger.
- **Not Urgent:** Relevant bushfire information that does not require immediate action, such as general updates, recovery information, or reports about past events.
- **Not Useful:** Information that is unrelated, unclear, duplicated, promotional, or does not provide useful information for emergency response.

The dataset should contain short text samples such as social media posts, emergency messages, public reports, or news-style statements. Each sample should have one urgency label.

## Candidate Datasets

### 1. TREC Incident Streams Dataset

The TREC Incident Streams dataset is the most relevant option for this task. It contains social media posts collected during emergency and crisis events. The posts are labelled by information type and priority or criticality for emergency response.

This dataset could support the FireFusion urgency classifier because its priority labels are closely related to the proposed urgent and not urgent categories. However, the original labels would need to be reviewed and converted into the three FireFusion labels: urgent, not urgent, and not useful.

The full TREC Incident Streams collection contains more than 136,000 annotated posts from 98 crisis events. It includes different emergencies rather than only bushfires, so bushfire-related samples may need to be filtered or supplemented with additional data.

Source: https://www.nist.gov/publications/incident-streams-2021-deep-end-deeper-annotations-and-evaluations-twitter

### 2. HumAID Dataset

The HumAID dataset contains approximately 77,000 human-labelled tweets collected from 19 natural disaster events between 2016 and 2019. These events include wildfires, floods, hurricanes, and earthquakes.

The dataset includes useful categories such as requests or urgent needs, injured or dead people, displaced people and evacuations, infrastructure damage, caution and advice, other relevant information, and not humanitarian.

For FireFusion, posts about urgent needs, evacuations, injuries, and immediate danger could be mapped to the urgent category. General disaster updates could be mapped to not urgent, while not humanitarian or unclear posts could be mapped to not useful.

A limitation is that the dataset covers several disaster types and does not directly provide the exact three urgency labels required by FireFusion. Therefore, its existing labels would need to be filtered and converted.

Source: https://crisisnlp.qcri.org/humaid_dataset.html

### 3. CrisisLexT26 Dataset

The CrisisLexT26 dataset contains social media posts collected from 26 crisis events that occurred during 2012 and 2013. Around 1,000 posts from each event were manually labelled for informativeness, information type, and information source.

This dataset could help identify content that belongs in the not useful category. Posts labelled as not informative or unrelated could be mapped to not useful. Informative posts could then be further reviewed and divided into urgent and not urgent categories.

A limitation is that CrisisLexT26 does not directly include urgency labels. It also contains different types of disasters rather than focusing only on bushfires. Therefore, additional manual labelling would be required before using it to train the FireFusion urgency classifier.

Source: https://www.crisislex.org/data-collections.html

## Proposed Label Mapping

The existing dataset labels will need to be converted into the three FireFusion urgency classes.

| FireFusion Label | Possible Source Labels or Content |
|---|---|
| **Urgent** | Evacuation warnings, people trapped, injuries, deaths, missing people, immediate requests for help, active fire threats, and critical infrastructure damage |
| **Not Urgent** | General fire updates, recovery information, completed evacuations, damage reports without immediate danger, safety advice, and background information |
| **Not Useful** | Unrelated content, advertisements, jokes, duplicated posts, unclear messages, rumours without useful details, and non-informative content |

Some source labels may not clearly fit into one FireFusion class. These samples should be manually reviewed to ensure consistent and accurate labelling.

## Dataset Limitations

The available datasets do not exactly match the FireFusion urgency classification requirements. Most crisis datasets include labels for information type, humanitarian relevance, or informativeness rather than the exact urgent, not urgent, and not useful classes.

Another limitation is that many datasets contain multiple disaster types, including floods, earthquakes, hurricanes, and wildfires. The language used in these events may be different from Australian bushfire-related communication.

Social media data may also contain spelling mistakes, abbreviations, duplicated posts, incomplete information, and informal language. Some older datasets may have missing posts because the original social media content was deleted or made unavailable.

Because of these limitations, the selected data will require filtering, label conversion, manual checking, and possibly additional synthetic or manually annotated bushfire examples.

## Recommended Approach

The recommended approach is to use the TREC Incident Streams dataset as the main starting point because it already includes information about the priority or criticality of crisis-related posts.

HumAID can be used as a secondary dataset because it contains useful categories related to evacuations, injuries, urgent needs, warnings, and other humanitarian information. CrisisLexT26 can help identify informative and non-informative posts, especially for the not useful category.

The datasets should not be combined without reviewing their labels. A common FireFusion labelling guide should first be created. Selected samples should then be converted into the urgent, not urgent, and not useful classes.

Additional Australian bushfire examples may be manually collected or synthetically created to improve the relevance of the final dataset. These examples should include evacuation warnings, emergency alerts, fire updates, community information, unrelated posts, and misleading or unclear messages.

## Conclusion

No single public dataset fully matches the FireFusion urgency classification task. TREC Incident Streams is the most suitable starting point because it includes crisis-related priority information. HumAID and CrisisLexT26 can provide additional useful and non-useful examples.

The final dataset should be created by filtering relevant crisis posts, converting the original labels into the three FireFusion classes, manually reviewing unclear samples, and adding Australian bushfire-specific examples where required.