/**
    This script returns the free election flag state for the election with the id provided as input.

    @param electionId (UInt64): The election identifier for the Election whose free status is to be determined
    @return Bool: True if the transaction fees related to this Election are to be paid exclusively by the service account. False if the fees are to be split instead. 
**/
import ElectionStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

access(all) fun main(electionId: UInt64): Bool {
    // Grab a public reference to the Election with the electionId provided
    let electionPublicRef: &{ElectionStandard.ElectionPublic} = VoteBooth.getElectionPublicReference(electionId: electionId) ??
    panic(
        "Unable to ge a valid &{ElectionStandard.ElectionPublic} from the VoteBooth contract for Election ".concat(electionId.toString())
    )

    return electionPublicRef.isElectionFree()
}