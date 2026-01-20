/**
    This transaction withdraws all the Ballots currently in storage, counts them computes the tally for a given Election. This transaction uses the ElectionStandard.ElectionAdmin entitlement to access the privileged function used to compute this result. Because I cannot return anything from a transaction, this particular transaction script logs out the electionResults dictionary for the election in question.

    @param electionId (UInt64) The election identifier for the Election whose tally is to be computed.
    @param batchSize (UInt) The number of Ballot to process per batch, to prevent the process from exceeding computation limits
**/

import ElectionStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516
import BallotStandard from 0x287f5c8b0865c516

transaction(electionId: UInt64) {
    let electionIndexRef: &{VoteBooth.ElectionIndexPublic}
    let electionStoragePath: StoragePath
    let electionRef: auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election

    prepare(signer: auth(ElectionStandard.ElectionAdmin, BorrowValue) &Account) {
        self.electionIndexRef = signer.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `signer.address.toString()`"
        )

        self.electionStoragePath = self.electionIndexRef.getElectionStoragePath(electionId: electionId) ??
        panic(
            "Unable to get a StoragePath for Election `electionId.toString()` from the ElectionIndexPublic from account `signer.address.toString()`"
        )

        self.electionRef = signer.storage.borrow<auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election>(from: self.electionStoragePath) ??
        panic(
            "Unable to get a valid auth(ElectionStandard.ElectionAdmin) &ElectionStandard.Election at `self.electionStoragePath.toString()` from account `signer.address.toString()`"
        )

        // Finish the Election by extracting the Ballot options to a dedicated internal array
        self.electionRef.withdrawBallots()
    }

    execute {
    }
}