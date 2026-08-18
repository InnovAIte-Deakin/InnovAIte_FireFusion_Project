# Urgency Classification Dataset Research

## Objective

The objective of this research is to identify and evaluate suitable datasets for urgency classification that could be integrated into the FireFusion misinformation detection system. The selected dataset should help classify how urgent a social media post or message is during emergency events such as bushfires.

## Urgency Classification

Urgency classification is the process of assigning a priority level to a crisis-related message. It helps identify which posts may require immediate attention and which posts are less urgent.

For FireFusion, urgency classification could help prioritise messages such as evacuation requests, immediate danger reports, missing-person information, emergency warnings and requests for assistance.

## Dataset Candidates

I reviewed two crisis-related datasets that could support this task:

1. TREC Incident Streams
2. CrisisLexT26

TREC Incident Streams is more suitable for urgency classification because it already includes a priority label for each crisis-related post. CrisisLexT26 contains useful crisis tweets, but its main labels focus on informativeness, information type and source rather than urgency.

## Selected Dataset: TREC Incident Streams

The selected dataset is TREC Incident Streams, also known as TREC-IS.

TREC-IS contains social media posts collected during different emergency events, including wildfires, floods, earthquakes, hurricanes, explosions and other incidents.

The dataset was created to help emergency-response systems identify useful and important information from social media. Each post includes information-type annotations and a priority label showing how important the message may be for an emergency responder.

## Priority Labels

The dataset uses four priority labels:

- Critical
- High
- Medium
- Low

Critical posts may include immediate danger, urgent requests for rescue or evacuation, or serious threats to life.

High-priority posts may contain important warnings, reports of injuries or major damage.

Medium-priority posts may provide useful situation updates that do not require immediate action.

Low-priority posts may contain general discussion, advice, opinions or less important information.

## Relevant Information Types

TREC-IS also includes information categories that may be useful for FireFusion, such as:

- search and rescue requests
- requests for assistance
- affected individuals
- infrastructure damage
- evacuation information
- warnings
- location information
- official updates

These categories could help the model understand why a post has been assigned a particular urgency level.

## Suitability for FireFusion

TREC-IS is suitable for FireFusion because the project needs to identify urgent information during bushfire emergencies.

For example, a post requesting immediate evacuation assistance should receive a higher priority than a post containing general discussion about bushfire conditions.

The dataset could be used to add an urgency classification output to the current DeBERTa system while keeping misinformation detection as a separate task.

## Proposed FireFusion Data Format

The selected fields could be converted into a simple FireFusion format:

```text
claim
urgency_label
```

Example:

```json
{
  "claim": "Residents near the fire zone must evacuate immediately.",
  "urgency_label": "critical"
}
```

A numerical label mapping could be:

```text
0 = low
1 = medium
2 = high
3 = critical
```

## Dataset Exploration

The following dataset exploration checks were completed:

- identified the available files and formats
- displayed the number of records
- reviewed the column names
- checked for missing values
- calculated the number of posts in each priority class
- displayed sample posts from each urgency level
- identified wildfire-related records
- reviewed whether the classes are balanced
- checked whether the text requires cleaning

## Strengths

- Contains real crisis-related social media posts.
- Includes direct priority labels.
- Covers wildfires and several other disaster types.
- Includes useful emergency-information categories.
- Supports multi-class urgency classification.
- Can be adapted for a future multi-task DeBERTa model.

## Limitations

- The posts may contain spelling errors, abbreviations and informal language.
- Some original social media posts may need to be downloaded using their post IDs.
- The dataset includes events from different countries and is not limited to Victoria.
- The four priority classes are imbalanced, with far fewer Critical records than Low records.
- The label definitions must be checked carefully before combining different TREC-IS versions.
- Access and usage conditions must be confirmed before including the data in FireFusion.


## Dataset Exploration Results

The selected TREC Incident Streams dataset was explored using a Python script.

The dataset contains:

- 71 crisis events
- 97,577 labelled tweets
- 9 available fields
- 9,427 wildfire or fire-related tweets

The main fields are:

- `postText`
- `postPriority`
- `postCategories`
- `eventType`
- `eventID`
- `postID`

### Missing Values

The exploration found:

- 21,118 records with missing `postText`
- 54 records with missing `postCategories`
- 52,017 records with missing `multipleJudgements`

The missing `multipleJudgements` values are less important because this field is not required for urgency classification. However, records with missing `postText` should be removed before model training.

### Priority Label Distribution

The urgency labels are distributed as follows:

- Low: 64,090
- Medium: 20,487
- High: 11,413
- Critical: 1,585
- Unknown: 2

The dataset is imbalanced because most records belong to the Low class, while the Critical class is much smaller.

### Event Type Distribution

The dataset includes several emergency types, including:

- wildfire
- fire
- flood
- earthquake
- typhoon
- shooting
- bombing
- explosion
- storm
- tornado
- pandemic
- hostage incidents

There are 9,427 wildfire and fire-related tweets, which makes the dataset relevant to FireFusion.

### Exploration Conclusion

The dataset is suitable for urgency classification because it contains direct priority labels, a large number of crisis-related messages and 9,427 wildfire or fire-related tweets.

The main issues are missing text and class imbalance, especially the small number of Critical records compared with Low records.

## Recommendation

TREC Incident Streams is recommended for the FireFusion urgency classification feature.

It is more suitable than CrisisLexT26 because it directly provides priority labels that match the purpose of urgency classification. It also contains wildfire and fire-related events and emergency-information categories that are relevant to FireFusion.

The dataset has now been obtained and explored using a Python script. Before future model development, the data should be cleaned by:

- removing records with missing text
- removing the two Unknown priority labels
- checking duplicate posts
- reviewing class imbalance
- considering class weights or balanced sampling
- selecting wildfire-related records for FireFusion-focused experiments

## References

- TREC Incident Streams: https://www.dcs.gla.ac.uk/~richardm/TREC_IS/
- TREC-IS task information: https://www.dcs.gla.ac.uk/~richardm/TREC_IS/2020/participate.html
- CrisisLex datasets: https://crisislex.org/data-collections.html